"use strict";

require([
    "jquery",
    "splunkjs/splunk",
    "splunk.util",
    "splunkjs/mvc/simplexml/ready!"
], function($, splunkjs, splunkUtil) {
    const appName = "TA-WhoisXmlApiQuery";
    const namespace = {owner: "nobody", app: appName, sharing: "app"};
    const passwordName = "whoisxmlapi_api_key";
    const button = $("#setup_button");
    const input = $("#password_input");
    const success = $("#main_container .success");
    const error = $("#main_container .error");
    const details = $("#error_details");

    button.on("click", async function(event) {
        event.preventDefault();
        if (button.prop("disabled")) {
            return;
        }
        success.hide();
        error.hide();
        details.empty().hide();
        const password = input.val();
        if (typeof password !== "string" || !password.trim()) {
            details.text("Enter an API key before completing setup.").show();
            error.show();
            input.trigger("focus");
            return;
        }

        button.prop("disabled", true);
        let stage = "saving the API key";
        try {
            const service = new splunkjs.Service(new splunkjs.SplunkWebHttp(), namespace);
            const passwords = service.storagePasswords(namespace);
            await passwords.fetch();
            const existing = passwords.item(":" + passwordName + ":");
            if (existing) {
                await existing.update({password: password});
            } else {
                await passwords.create({name: passwordName, realm: "", password: password});
            }
            input.val("");

            stage = "marking the app as configured";
            const apps = service.apps();
            await apps.fetch();
            const app = apps.item(appName);
            if (!app) {
                throw new Error("The installed app is unavailable.");
            }
            await new Promise((resolve, reject) => {
                app.update({configured: true}, failure => {
                    if (failure) {
                        reject(failure);
                    } else {
                        resolve();
                    }
                });
            });

            stage = "reloading the app";
            await new Promise((resolve, reject) => {
                app.reload(failure => {
                    if (failure) {
                        reject(failure);
                    } else {
                        resolve();
                    }
                });
            });
            success.show();
            window.location.assign(splunkUtil.make_url("/app/" + appName));
        } catch (failure) {
            const status = failure && typeof failure.status === "number"
                ? " (HTTP " + failure.status + ")" : "";
            details.text("Setup failed while " + stage + status +
                ". Check your Splunk permissions and retry.").show();
            error.show();
        } finally {
            button.prop("disabled", false);
        }
    });
});
