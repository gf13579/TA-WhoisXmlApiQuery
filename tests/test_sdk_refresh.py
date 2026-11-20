import csv
import importlib.metadata
import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, call, patch


BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

import splunklib.binding
import whoisxmlapi
import wxa


class SdkRefreshTests(unittest.TestCase):
    def test_streaming_command_loads_credentials_and_caches_results(self):
        distribution = importlib.metadata.distribution("splunk-sdk")
        self.assertEqual(
            Path(distribution.locate_file("splunklib/__init__.py")).resolve(),
            (BIN / "splunklib" / "__init__.py").resolve(),
        )

        atom = (
            b'<feed xmlns="http://www.w3.org/2005/Atom" '
            b'xmlns:s="http://dev.splunk.com/ns/rest">'
            b'<entry><title>test</title><link rel="alternate" '
            b'href="/servicesNS/nobody/TA-WhoisXmlApiQuery/storage/passwords/test"/>'
            b'<content type="text/xml"><s:dict>'
            b'<s:key name="username">whoisxmlapi_api_key</s:key>'
            b'<s:key name="clear_password">test-key</s:key>'
            b"</s:dict></content></entry></feed>"
        )
        connection = MagicMock()
        response = connection.getresponse.return_value
        response.status = 200
        response.reason = "OK"
        response.getheader.return_value = "close"
        response.getheaders.return_value = []
        response.read.return_value = atom

        with TemporaryDirectory() as directory:
            info_path = Path(directory) / "info.csv"
            with info_path.open("w", newline="") as info_file:
                writer = csv.writer(info_file)
                writer.writerow(
                    [
                        "ppc_app",
                        "rt_earliest",
                        "rt_latest",
                        "auth_token",
                        "splunkd_uri",
                        "ppc_user",
                    ]
                )
                writer.writerow(
                    [
                        "TA-WhoisXmlApiQuery",
                        "",
                        "",
                        "Splunk test",
                        "http://127.0.0.1:8089",
                        "nobody",
                    ]
                )

            command = whoisxmlapi.whoisxmlapiCommand()
            input_file = io.StringIO(
                f"infoPath:{info_path}\n\ndomain\nexample.com\nexample.com\nexample.org\n"
            )
            output_file = io.BytesIO()

            with (
                patch("splunklib.binding.client.HTTPConnection", return_value=connection),
                patch("tempfile.tempdir", None),
                patch.object(
                    wxa,
                    "submit_query_single",
                    side_effect=[{"registrarName": "First"}, {"registrarName": "Second"}],
                ) as submit,
            ):
                command.process(["whoisxmlapi.py", "__EXECUTE__"], input_file, output_file)

        output = output_file.getvalue().decode().lstrip("\r\n")
        rows = list(csv.DictReader(io.StringIO(output)))
        self.assertEqual(
            [row["domain"] for row in rows],
            ["example.com", "example.com", "example.org"],
        )
        self.assertEqual(
            [row["registrarName"] for row in rows], ["First", "First", "Second"]
        )
        self.assertEqual(
            submit.call_args_list,
            [call("test-key", "example.com"), call("test-key", "example.org")],
        )
        headers = connection.request.call_args.args[3]
        self.assertEqual(headers["User-Agent"], f"splunk-sdk-python/{distribution.version}")
        self.assertEqual(headers["Authorization"], "Splunk test")

    def test_getinfo_reports_streaming(self):
        output_file = io.BytesIO()
        with patch("tempfile.tempdir", None):
            whoisxmlapi.whoisxmlapiCommand().process(
                ["whoisxmlapi.py", "__GETINFO__"], io.StringIO("\n"), output_file
            )
        output = output_file.getvalue().decode().lstrip("\r\n")
        configuration = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual(configuration["streaming"], "1")

    def test_older_python_exits_before_loading_the_sdk(self):
        source = (BIN / "whoisxmlapi.py").read_bytes()
        code = compile(source, str(BIN / "whoisxmlapi.py"), "exec")

        with patch.object(sys, "version_info", (3, 9)):
            with self.assertRaisesRegex(SystemExit, "requires Python 3.13 or newer"):
                exec(code, {"__name__": "unsupported_python"})


if __name__ == "__main__":
    unittest.main()
