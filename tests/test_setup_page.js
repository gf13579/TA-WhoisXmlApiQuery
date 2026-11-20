"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(
    path.join(__dirname, "../appserver/static/javascript/setup_page.js"), "utf8"
);

function fixture(options = {}) {
    const calls = [];
    const elements = new Map();
    const redirects = [];
    function $(selector) {
        if (!elements.has(selector)) {
            elements.set(selector, {
                value: "",
                visible: false,
                disabled: false,
                content: "",
                on(event, handler) { this.handler = handler; return this; },
                prop(name, value) {
                    if (value === undefined) return this[name];
                    this[name] = value;
                    return this;
                },
                val(value) {
                    if (value === undefined) return this.value;
                    this.value = value;
                    return this;
                },
                hide() { this.visible = false; return this; },
                show() { this.visible = true; return this; },
                empty() { this.content = ""; return this; },
                text(value) { this.content = value; return this; },
                trigger(event) { this.lastEvent = event; return this; }
            });
        }
        return elements.get(selector);
    }
    async function operation(name, data) {
        calls.push({name, data});
        if (options.fail === name) {
            throw {status: 403, responseText: "<script>secret</script>"};
        }
        if (options.wait && options.wait[name]) await options.wait[name];
    }
    const passwords = {
        fetch: () => operation("passwords.fetch"),
        item: name => {
            assert.equal(name, ":whoisxmlapi_api_key:");
            return options.existing ? {update: data => operation("update", data)} : null;
        },
        create: data => operation("create", data)
    };
    class Service {
        constructor(http, namespace) {
            assert.deepEqual(JSON.parse(JSON.stringify(namespace)), {
                owner: "nobody", app: "TA-WhoisXmlApiQuery", sharing: "app"
            });
        }
        storagePasswords() { return passwords; }
        configurations() {
            throw new Error("Configuration stanzas can belong to another app.");
        }
        apps() {
            return {
                fetch: () => operation("apps.fetch"),
                item: name => {
                    assert.equal(name, "TA-WhoisXmlApiQuery");
                    return {
                        update(data, callback) {
                            operation("configure", data).then(
                                () => { if (callback) callback(null); },
                                failure => { if (callback) callback(failure); }
                            );
                        },
                        reload(callback) {
                            operation("reload").then(
                                () => { if (callback) callback(null); },
                                failure => { if (callback) callback(failure); }
                            );
                        }
                    };
                }
            };
        }
    }
    vm.runInNewContext(source, {
        require(dependencies, callback) {
            assert.ok(dependencies.includes("splunkjs/mvc/simplexml/ready!"));
            callback($, {Service, SplunkWebHttp: class {}}, {
                make_url: url => "/en-US" + url
            });
        },
        window: {location: {assign: url => redirects.push(url)}}
    });
    return {
        $, calls, redirects,
        click: () => $("#setup_button").handler({preventDefault() {}})
    };
}

test("rejects an empty key without contacting Splunk", async () => {
    const page = fixture();
    page.$("#password_input").val("   ");
    await page.click();
    assert.equal(page.calls.length, 0);
    assert.equal(page.$("#main_container .error").visible, true);
    assert.match(page.$("#error_details").content, /Enter an API key/);
});

test("waits for credential save, configuration, and reload before redirecting", async () => {
    let save, configure, reload;
    const page = fixture({wait: {
        create: new Promise(resolve => { save = resolve; }),
        configure: new Promise(resolve => { configure = resolve; }),
        reload: new Promise(resolve => { reload = resolve; })
    }});
    page.$("#password_input").val("test-key");
    const pending = page.click();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(page.$("#setup_button").disabled, true);
    assert.equal(page.calls.at(-1).name, "create");
    await page.click();
    assert.equal(page.calls.filter(call => call.name === "create").length, 1);
    assert.equal(page.redirects.length, 0);
    save();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(page.calls.at(-1).name, "configure");
    assert.equal(page.redirects.length, 0);
    configure();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(page.calls.at(-1).name, "reload");
    assert.equal(page.redirects.length, 0);
    reload();
    await pending;
    assert.deepEqual(page.redirects, ["/en-US/app/TA-WhoisXmlApiQuery"]);
    assert.equal(page.$("#password_input").val(), "");
    const credential = page.calls.find(call => call.name === "create").data;
    assert.deepEqual(JSON.parse(JSON.stringify(credential)), {
        name: "whoisxmlapi_api_key", realm: "", password: "test-key"
    });
});

test("updates an existing credential and configures the target app without inherited stanzas", async () => {
    const page = fixture({existing: true});
    page.$("#password_input").val("replacement-key");
    await page.click();
    assert.equal(page.calls.some(call => call.name === "create"), false);
    assert.equal(page.calls.find(call => call.name === "update").data.password, "replacement-key");
    assert.deepEqual(JSON.parse(JSON.stringify(page.calls.find(call => call.name === "configure").data)), {
        configured: true
    });
    assert.equal(page.redirects.length, 1);
});

for (const stage of ["create", "update", "configure", "reload"]) {
    test(`${stage} failure stays on setup and permits retry without exposing responses`, async () => {
        const page = fixture({fail: stage, existing: stage === "update"});
        page.$("#password_input").val("test-key");
        await page.click();
        assert.equal(page.redirects.length, 0);
        assert.equal(page.$("#main_container .success").visible, false);
        assert.equal(page.$("#main_container .error").visible, true);
        assert.equal(page.$("#setup_button").disabled, false);
        assert.match(page.$("#error_details").content, /HTTP 403/);
        assert.doesNotMatch(page.$("#error_details").content, /secret|test-key|<script>/);
        if (stage === "create" || stage === "update") {
            assert.equal(page.calls.some(call => call.name === "configure"), false);
        }
    });
}
