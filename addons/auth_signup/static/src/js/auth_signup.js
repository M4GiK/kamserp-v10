openerp.auth_signup = function(instance) {
    instance.auth_signup = instance.auth_signup || {};
    var _t = instance.web._t;

    instance.web.Login.include({
        init: function() {
            this._super.apply(this, arguments);
            this.signup_enabled = false;
            this.reset_password_enabled = false;
            this.on('change:login-mode', this, function() {
                /*
                 * Switches the login box to the select mode
                 * whith mode == [default|signup|reset]
                 */
                var self = this;
                var mode = this.get('login-mode') || 'default';
                self.$('*[data-modes]').each(function() {
                    var modes = $(this).data('modes').split(/\s+/);
                    $(this).toggle(modes.indexOf(mode) > -1);
                });
                self.$('a.oe_signup_signup:visible').toggle(this.signup_enabled);
                self.$('a.oe_signup_reset_password:visible').toggle(this.reset_password_enabled);
            });
        },
        start: function() {
            var self = this;
            this.set({ 'login-mode': 'default' });
            return this._super().then(function() {
                // to switch between the signup and regular login form
                self.$('a.oe_signup_signup').click(function(ev) {
                    self.set({ 'login-mode': 'signup' });
                    return false;
                });
                self.$('a.oe_signup_back').click(function(ev) {
                    self.set({ 'login-mode': 'default' });
                    delete self.params.token;
                    return false;
                });

                var dblist = self.db_list || [];
                var dbname = self.params.db || (dblist.length === 1 ? dblist[0] : null);

                // if there is an error message in params, show it then forget it
                if (self.params.error_message) {
                    self.show_error(self.params.error_message);
                    delete self.params.error_message;
                }

                // in case of a signup, retrieve the user information from the token
                if (dbname && self.params.token) {
                    self.rpc("/auth_signup/retrieve", {dbname: dbname, token: self.params.token})
                        .done(self.on_token_loaded)
                        .fail(self.on_token_failed);
                }
                if (dbname && self.params.login) {
                    self.$("form input[name=login]").val(self.params.login);
                }

                // bind reset password link
                self.$('a.oe_signup_reset_password').click(self.do_reset_password);

                if (dbname) {
                    self.rpc("/auth_signup/get_config", {dbname: dbname}).done(function(result) {
                        self.signup_enabled = result.signup;
                        self.reset_password_enabled = result.reset_password;
                    });
                }
            });
        },

        on_token_loaded: function(result) {
            // select the right the database
            this.selected_db = result.db;
            this.on_db_loaded([result.db]);
            if (result.token) {
                // switch to signup mode, set user name and login
                this.set({ 'login-mode': 'signup' });
                this.$("form input[name=name]").val(result.name).attr("readonly", "readonly");
                if (result.login) {
                    this.$("form input[name=login]").val(result.login).attr("readonly", "readonly");
                } else {
                    this.$("form input[name=login]").val(result.email);
                }
            } else {
                // remain in login mode, set login if present
                delete this.params.token;
                this.set({ 'login-mode': 'default' });
                this.$("form input[name=login]").val(result.login || "");
            }
        },

        on_token_failed: function(result, ev) {
            if (ev) {
                ev.preventDefault();
            }
            this.show_error(_t("Invalid signup token"));
            delete this.params.db;
            delete this.params.token;
            this.set({ 'login-mode': 'default' });
        },

        on_submit: function(ev) {
            if (ev) {
                ev.preventDefault();
            }
            var login_mode = this.get('login-mode');
            if (login_mode === 'signup' || login_mode === 'reset') {
                // signup user (or reset password)
                var db = this.$("form [name=db]").val();
                var name = this.$("form input[name=name]").val();
                var login = this.$("form input[name=login]").val();
                var password = this.$("form input[name=password]").val();
                var confirm_password = this.$("form input[name=confirm_password]").val();
                if (!db) {
                    this.do_warn(_t("Login"), _t("No database selected !"));
                    return false;
                } else if (!name) {
                    this.do_warn(_t("Login"), _t("Please enter a name."));
                    return false;
                } else if (!login) {
                    this.do_warn(_t("Login"), _t("Please enter a username."));
                    return false;
                } else if (!password || !confirm_password) {
                    this.do_warn(_t("Login"), _t("Please enter a password and confirm it."));
                    return false;
                } else if (password !== confirm_password) {
                    this.do_warn(_t("Login"), _t("Passwords do not match; please retype them."));
                    return false;
                }
                var params = {
                    dbname : db,
                    token: this.params.token || "",
                    name: name,
                    login: login,
                    password: password,
                };

                var self = this,
                    super_ = this._super;
                this.rpc('/auth_signup/signup', params)
                    .done(function(result) {
                        if (result.error) {
                            self.show_error(result.error);
                        } else {
                            super_.apply(self, [ev]);
                        }
                    });
            } else {
                // regular login
                this._super(ev);
            }
        },

        do_reset_password: function(ev) {
            if (ev) {
                ev.preventDefault();
            }
            var db = this.$("form [name=db]").val();
            var login = this.$("form input[name=login]").val();
            if (!db) {
                this.do_warn(_t("Login"), _t("No database selected !"));
                return false;
            } else if (!login) {
                this.do_warn(_t("Login"), _t("Please enter a username or email address."));
                return false;
            }
            var params = {
                dbname : db,
                login: login,
            };
            var url = "/auth_signup/reset_password?" + $.param(params);
            window.location = url;
        },
    });
};
