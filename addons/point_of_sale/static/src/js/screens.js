
// This file contains the Screens definitions. Screens are the
// content of the right pane of the pos, containing the main functionalities. 
//
// Screens must be defined and named in chrome.js before use.
//
// Screens transitions are controlled by the Gui.
//  gui.set_startup_screen() sets the screen displayed at startup
//  gui.set_default_screen() sets the screen displayed for new orders
//  gui.show_screen() shows a screen
//  gui.back() goes to the previous screen
//
// Screen state is saved in the order. When a new order is selected,
// a screen is displayed based on the state previously saved in the order.
// this is also done in the Gui with:
//  gui.show_saved_screen()
//
// All screens inherit from ScreenWidget. The only addition from the base widgets
// are show() and hide() which shows and hides the screen but are also used to 
// bind and unbind actions on widgets and devices. The gui guarantees
// that only one screen is shown at the same time and that show() is called after all
// hide()s
//
// Each Screens must be independant from each other, and should have no 
// persistent state outside the models. Screen state variables are reset at
// each screen display. A screen can be called with parameters, which are
// to be used for the duration of the screen only. 

openerp.point_of_sale.load_screens = function load_screens(instance, module){ //module is instance.point_of_sale
    "use strict";

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    var round_pr = instance.web.round_precision

    /*--------------------------------------*\
     |          THE SCREEN WIDGET           |
    \*======================================*/
    
    // The screen widget is the base class inherited
    // by all screens.

    module.ScreenWidget = module.PosBaseWidget.extend({

        init: function(parent,options){
            this._super(parent,options);
            this.hidden = false;
        },

        barcode_product_screen:         'products',     //if defined, this screen will be loaded when a product is scanned

        // what happens when a product is scanned : 
        // it will add the product to the order and go to barcode_product_screen. 
        barcode_product_action: function(code){
            var self = this;
            if(self.pos.scan_product(code)){
                if(self.barcode_product_screen){ 
                    self.gui.show_screen(self.barcode_product_screen);
                }
            }else{
                self.gui.show_popup('error-barcode',code.code);
            }
        },

        // what happens when a cashier id barcode is scanned.
        // the default behavior is the following : 
        // - if there's a user with a matching barcode, put it as the active 'cashier', go to cashier mode, and return true
        // - else : do nothing and return false. You probably want to extend this to show and appropriate error popup... 
        barcode_cashier_action: function(code){
            var users = this.pos.users;
            for(var i = 0, len = users.length; i < len; i++){
                if(users[i].barcode === code.code){
                    this.pos.set_cashier(users[i]);
                    this.chrome.widget.username.renderElement();
                    return true;
                }
            }
            this.gui.show_popup('error-barcode',code.code);
            return false;
        },
        
        // what happens when a client id barcode is scanned.
        // the default behavior is the following : 
        // - if there's a user with a matching barcode, put it as the active 'client' and return true
        // - else : return false. 
        barcode_client_action: function(code){
            var partner = this.pos.db.get_partner_by_barcode(code.code);
            if(partner){
                this.pos.get_order().set_client(partner);
                return true;
            }
            this.gui.show_popup('error-barcode',code.code);
            return false;
        },
        
        // what happens when a discount barcode is scanned : the default behavior
        // is to set the discount on the last order.
        barcode_discount_action: function(code){
            var last_orderline = this.pos.get_order().get_last_orderline();
            if(last_orderline){
                last_orderline.set_discount(code.value)
            }
        },
        // What happens when an invalid barcode is scanned : shows an error popup.
        barcode_error_action: function(code){
            this.gui.show_popup('error-barcode',code.code);
        },

        // this method shows the screen and sets up all the widget related to this screen. Extend this method
        // if you want to alter the behavior of the screen.
        show: function(){
            var self = this;

            this.hidden = false;
            if(this.$el){
                this.$el.removeClass('oe_hidden');
            }

            this.pos.barcode_reader.set_action_callback({
                'cashier': self.barcode_cashier_action ? function(code){ self.barcode_cashier_action(code); } : undefined ,
                'product': self.barcode_product_action ? function(code){ self.barcode_product_action(code); } : undefined ,
                'client' : self.barcode_client_action ?  function(code){ self.barcode_client_action(code);  } : undefined ,
                'discount': self.barcode_discount_action ? function(code){ self.barcode_discount_action(code); } : undefined,
                'error'   : self.barcode_error_action ?  function(code){ self.barcode_error_action(code);   } : undefined,
            });
        },

        // this method is called when the screen is closed to make place for a new screen. this is a good place
        // to put your cleanup stuff as it is guaranteed that for each show() there is one and only one close()
        close: function(){
            if(this.pos.barcode_reader){
                this.pos.barcode_reader.reset_action_callbacks();
            }
        },

        // this methods hides the screen. It's not a good place to put your cleanup stuff as it is called on the
        // POS initialization.
        hide: function(){
            this.hidden = true;
            if(this.$el){
                this.$el.addClass('oe_hidden');
            }
        },

        // we need this because some screens re-render themselves when they are hidden
        // (due to some events, or magic, or both...)  we must make sure they remain hidden.
        // the good solution would probably be to make them not re-render themselves when they
        // are hidden. 
        renderElement: function(){
            this._super();
            if(this.hidden){
                if(this.$el){
                    this.$el.addClass('oe_hidden');
                }
            }
        },
    });

    /*--------------------------------------*\
     |          THE DOM CACHE               |
    \*======================================*/

    // The Dom Cache is used by various screens to improve
    // their performances when displaying many time the 
    // same piece of DOM.
    //
    // It is a simple map from string 'keys' to DOM Nodes.
    //
    // The cache empties itself based on usage frequency 
    // stats, so you may not always get back what
    // you put in.

    module.DomCache = instance.web.Class.extend({
        init: function(options){
            options = options || {};
            this.max_size = options.max_size || 2000;

            this.cache = {};
            this.access_time = {};
            this.size = 0;
        },
        cache_node: function(key,node){
            var cached = this.cache[key];
            this.cache[key] = node;
            this.access_time[key] = new Date().getTime();
            if(!cached){
                this.size++;
                while(this.size >= this.max_size){
                    var oldest_key = null;
                    var oldest_time = new Date().getTime();
                    for(var key in this.cache){
                        var time = this.access_time[key];
                        if(time <= oldest_time){
                            oldest_time = time;
                            oldest_key  = key;
                        }
                    }
                    if(oldest_key){
                        delete this.cache[oldest_key];
                        delete this.access_time[oldest_key];
                    }
                    this.size--;
                }
            }
            return node;
        },
        get_node: function(key){
            var cached = this.cache[key];
            if(cached){
                this.access_time[key] = new Date().getTime();
            }
            return cached;
        },
    });

    /*--------------------------------------*\
     |          THE SCALE SCREEN            |
    \*======================================*/

    // The scale screen displays the weight of
    // a product on the electronic scale.

    module.ScaleScreenWidget = module.ScreenWidget.extend({
        template:'ScaleScreenWidget',

        next_screen: 'products',
        previous_screen: 'products',

        show: function(){
            this._super();
            var self = this;
            var queue = this.pos.proxy_queue;

            this.set_weight(0);
            this.renderElement();

            this.hotkey_handler = function(event){
                if(event.which === 13){
                    self.order_product();
                    self.gui.show_screen(self.next_screen);
                }else if(event.which === 27){
                    self.gui.show_screen(self.previous_screen);
                }
            };

            $('body').on('keyup',this.hotkey_handler);

            this.$('.back').click(function(){
                self.gui.show_screen(self.previous_screen);
            });

            this.$('.next,.buy-product').click(function(){
                self.order_product();
                self.gui.show_screen(self.next_screen);
            });

            queue.schedule(function(){
                return self.pos.proxy.scale_read().then(function(weight){
                    self.set_weight(weight.weight);
                });
            },{duration:50, repeat: true});

        },
        get_product: function(){
            return this.gui.get_current_screen_param('product');
        },
        order_product: function(){
            this.pos.get_order().add_product(this.get_product(),{ quantity: this.weight });
        },
        get_product_name: function(){
            var product = this.get_product();
            return (product ? product.display_name : undefined) || 'Unnamed Product';
        },
        get_product_price: function(){
            var product = this.get_product();
            return (product ? product.price : 0) || 0;
        },
        set_weight: function(weight){
            this.weight = weight;
            this.$('.weight').text(this.get_product_weight_string());
            this.$('.computed-price').text(this.get_computed_price_string());
        },
        get_product_weight_string: function(){
            var product = this.get_product();
            var defaultstr = (this.weight || 0).toFixed(3) + ' Kg';
            if(!product || !this.pos){
                return defaultstr;
            }
            var unit_id = product.uom_id;
            if(!unit_id){
                return defaultstr;
            }
            var unit = this.pos.units_by_id[unit_id[0]];
            var weight = round_pr(this.weight || 0, unit.rounding);
            var weightstr = weight.toFixed(Math.ceil(Math.log(1.0/unit.rounding) / Math.log(10) ));
                weightstr += ' Kg';
            return weightstr;
        },
        get_computed_price_string: function(){
            return this.format_currency(this.get_product_price() * this.weight);
        },
        close: function(){
            var self = this;
            this._super();
            $('body').off('keyup',this.hotkey_handler);

            this.pos.proxy_queue.clear();
        },
    });
    module.Gui.define_screen({name: 'scale', widget: module.ScaleScreenWidget});

    /*--------------------------------------*\
     |         THE PRODUCT SCREEN           |
    \*======================================*/

    // The product screen contains the list of products,
    // The category selector and the order display.
    // It is the default screen for orders and the
    // startup screen for shops.
    //
    // There product screens uses many sub-widgets,
    // the code follows.


    /* ------------ The Numpad ------------ */
    
    // The numpad that edits the order lines.

    module.NumpadWidget = module.PosBaseWidget.extend({
        template:'NumpadWidget',
        init: function(parent, options) {
            this._super(parent);
            this.state = new module.NumpadState();
            var self = this;
        },
        start: function() {
            this.state.bind('change:mode', this.changedMode, this);
            this.changedMode();
            this.$el.find('.numpad-backspace').click(_.bind(this.clickDeleteLastChar, this));
            this.$el.find('.numpad-minus').click(_.bind(this.clickSwitchSign, this));
            this.$el.find('.number-char').click(_.bind(this.clickAppendNewChar, this));
            this.$el.find('.mode-button').click(_.bind(this.clickChangeMode, this));
        },
        clickDeleteLastChar: function() {
            return this.state.deleteLastChar();
        },
        clickSwitchSign: function() {
            return this.state.switchSign();
        },
        clickAppendNewChar: function(event) {
            var newChar;
            newChar = event.currentTarget.innerText || event.currentTarget.textContent;
            return this.state.appendNewChar(newChar);
        },
        clickChangeMode: function(event) {
            var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
            return this.state.changeMode(newMode);
        },
        changedMode: function() {
            var mode = this.state.get('mode');
            $('.selected-mode').removeClass('selected-mode');
            $(_.str.sprintf('.mode-button[data-mode="%s"]', mode), this.$el).addClass('selected-mode');
        },
    });

    /* ---------- The Action Pad ---------- */
    
    // The action pad contains the payment button and the 
    // customer selection button

    module.ActionpadWidget = module.PosBaseWidget.extend({
        template: 'ActionpadWidget',
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.pay').click(function(){
                self.gui.show_screen('payment');
            });
            this.$('.set-customer').click(function(){
                self.gui.show_screen('clientlist');
            });
        }
    });

    /* --------- The Order Widget --------- */
    
    // Displays the current Order.

    module.OrderWidget = module.PosBaseWidget.extend({
        template:'OrderWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);

            this.numpad_state = options.numpad_state;
            this.numpad_state.reset();
            this.numpad_state.bind('set_value',   this.set_value, this);

            this.pos.bind('change:selectedOrder', this.change_selected_order, this);

            this.line_click_handler = function(event){
                self.pos.get_order().select_orderline(this.orderline);
                self.numpad_state.reset();
            };

            if (this.pos.get_order()) {
                this.bind_order_events();
            }

        },
        set_value: function(val) {
        	var order = this.pos.get_order();
        	if (order.get_selected_orderline()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity'){
                    order.get_selected_orderline().set_quantity(val);
                }else if( mode === 'discount'){
                    order.get_selected_orderline().set_discount(val);
                }else if( mode === 'price'){
                    order.get_selected_orderline().set_unit_price(val);
                }
        	}
        },
        change_selected_order: function() {
            if (this.pos.get_order()) {
                this.bind_order_events();
                this.numpad_state.reset();
                this.renderElement();
            }
        },
        orderline_add: function(){
            this.numpad_state.reset();
            this.renderElement('and_scroll_to_bottom');
        },
        orderline_remove: function(line){
            this.remove_orderline(line);
            this.numpad_state.reset();
            this.update_summary();
        },
        orderline_change: function(line){
            this.rerender_orderline(line);
            this.update_summary();
        },
        bind_order_events: function() {
            var order = this.pos.get_order();
                order.unbind('change:client', this.update_summary, this);
                order.bind('change:client',   this.update_summary, this);
                order.unbind('change',        this.update_summary, this);
                order.bind('change',          this.update_summary, this);

            var lines = order.orderlines;
                lines.unbind('add',     this.orderline_add,    this);
                lines.bind('add',       this.orderline_add,    this);
                lines.unbind('remove',  this.orderline_remove, this);
                lines.bind('remove',    this.orderline_remove, this); 
                lines.unbind('change',  this.orderline_change, this);
                lines.bind('change',    this.orderline_change, this);

        },
        render_orderline: function(orderline){
            var el_str  = openerp.qweb.render('Orderline',{widget:this, line:orderline}); 
            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];
                el_node.orderline = orderline;
                el_node.addEventListener('click',this.line_click_handler);

            orderline.node = el_node;
            return el_node;
        },
        remove_orderline: function(order_line){
            if(this.pos.get_order().get_orderlines().length === 0){
                this.renderElement();
            }else{
                order_line.node.parentNode.removeChild(order_line.node);
            }
        },
        rerender_orderline: function(order_line){
            var node = order_line.node;
            var replacement_line = this.render_orderline(order_line);
            node.parentNode.replaceChild(replacement_line,node);
        },
        // overriding the openerp framework replace method for performance reasons
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        renderElement: function(scrollbottom){
            var order  = this.pos.get_order();
            if (!order) {
                return;
            }
            var orderlines = order.get_orderlines();

            var el_str  = openerp.qweb.render('OrderWidget',{widget:this, order:order, orderlines:orderlines});

            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];


            var list_container = el_node.querySelector('.orderlines');
            for(var i = 0, len = orderlines.length; i < len; i++){
                var orderline = this.render_orderline(orderlines[i]);
                list_container.appendChild(orderline);
            }

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            this.update_summary();

            if(scrollbottom){
                this.el.querySelector('.order-scroller').scrollTop = 100 * orderlines.length;
            }
        },
        update_summary: function(){
            var order = this.pos.get_order();
            var total     = order ? order.get_total_with_tax() : 0;
            var taxes     = order ? total - order.get_total_without_tax() : 0;

            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
        },
    });

    /* ------ The Product Categories ------ */
    
    // Display and navigate the product categories.
    // Also handles searches.
    //  - set_category() to change the displayed category
    //  - reset_category() to go to the root category
    //  - perform_search() to search for products
    //  - clear_search()   does what it says.

    module.ProductCategoriesWidget = module.PosBaseWidget.extend({
        template: 'ProductCategoriesWidget',
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            this.product_type = options.product_type || 'all';  // 'all' | 'weightable'
            this.onlyWeightable = options.onlyWeightable || false;
            this.category = this.pos.root_category;
            this.breadcrumb = [];
            this.subcategories = [];
            this.product_list_widget = options.product_list_widget || null;
            this.category_cache = new module.DomCache();
            this.set_category();
            
            this.switch_category_handler = function(event){
                self.set_category(self.pos.db.get_category_by_id(Number(this.dataset['categoryId'])));
                self.renderElement();
            };
            
            this.clear_search_handler = function(event){
                self.clear_search();
            };

            var search_timeout  = null;
            this.search_handler = function(event){
                clearTimeout(search_timeout);

                var query = this.value;

                search_timeout = setTimeout(function(){
                    self.perform_search(self.category, query, event.which === 13);
                },70);
            };
        },

        // changes the category. if undefined, sets to root category
        set_category : function(category){
            var db = this.pos.db;
            if(!category){
                this.category = db.get_category_by_id(db.root_category_id);
            }else{
                this.category = category;
            }
            this.breadcrumb = [];
            var ancestors_ids = db.get_category_ancestors_ids(this.category.id);
            for(var i = 1; i < ancestors_ids.length; i++){
                this.breadcrumb.push(db.get_category_by_id(ancestors_ids[i]));
            }
            if(this.category.id !== db.root_category_id){
                this.breadcrumb.push(this.category);
            }
            this.subcategories = db.get_category_by_id(db.get_category_childs_ids(this.category.id));
        },

        get_image_url: function(category){
            return window.location.origin + '/web/binary/image?model=pos.category&field=image_medium&id='+category.id;
        },

        render_category: function( category, with_image ){
            var cached = this.category_cache.get_node(category.id);
            if(!cached){
                if(with_image){
                    var image_url = this.get_image_url(category);
                    var category_html = QWeb.render('CategoryButton',{ 
                            widget:  this, 
                            category: category, 
                            image_url: this.get_image_url(category),
                        });
                        category_html = _.str.trim(category_html);
                    var category_node = document.createElement('div');
                        category_node.innerHTML = category_html;
                        category_node = category_node.childNodes[0];
                }else{
                    var category_html = QWeb.render('CategorySimpleButton',{ 
                            widget:  this, 
                            category: category, 
                        });
                        category_html = _.str.trim(category_html);
                    var category_node = document.createElement('div');
                        category_node.innerHTML = category_html;
                        category_node = category_node.childNodes[0];
                }
                this.category_cache.cache_node(category.id,category_node);
                return category_node;
            }
            return cached; 
        },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        renderElement: function(){
            var self = this;

            var el_str  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }

            this.el = el_node;

            var hasimages = false;  //if none of the subcategories have images, we don't display buttons with icons
            for(var i = 0; i < this.subcategories.length; i++){
                if(this.subcategories[i].image){
                    hasimages = true;
                    break;
                }
            }

            var list_container = el_node.querySelector('.category-list');
            if (list_container) { 
                if (!hasimages) {
                    list_container.classList.add('simple');
                } else {
                    list_container.classList.remove('simple');
                }
                for(var i = 0, len = this.subcategories.length; i < len; i++){
                    list_container.appendChild(this.render_category(this.subcategories[i],hasimages));
                };
            }

            var buttons = el_node.querySelectorAll('.js-category-switch');
            for(var i = 0; i < buttons.length; i++){
                buttons[i].addEventListener('click',this.switch_category_handler);
            }

            var products = this.pos.db.get_product_by_category(this.category.id); 
            this.product_list_widget.set_product_list(products); // FIXME: this should be moved elsewhere ... 

            this.el.querySelector('.searchbox input').addEventListener('keyup',this.search_handler);

            this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);

            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect($(this.el.querySelector('.searchbox input')));
            }
        },
        
        // resets the current category to the root category
        reset_category: function(){
            this.set_category();
            this.renderElement();
        },

        // empties the content of the search box
        clear_search: function(){
            var products = this.pos.db.get_product_by_category(this.category.id);
            this.product_list_widget.set_product_list(products);
            var input = this.el.querySelector('.searchbox input');
                input.value = '';
                input.focus();
        },
        perform_search: function(category, query, buy_result){
            if(query){
                var products = this.pos.db.search_product_in_category(category.id,query)
                if(buy_result && products.length === 1){
                        this.pos.get_order().add_product(products[0]);
                        this.clear_search();
                }else{
                    this.product_list_widget.set_product_list(products);
                }
            }else{
                var products = this.pos.db.get_product_by_category(this.category.id);
                this.product_list_widget.set_product_list(products);
            }
        },

    });

    /* --------- The Product List --------- */
    
    // Display the list of products. 
    // - change the list with .set_product_list()
    // - click_product_action(), passed as an option, tells
    //   what to do when a product is clicked. 

    module.ProductListWidget = module.PosBaseWidget.extend({
        template:'ProductListWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.model = options.model;
            this.productwidgets = [];
            this.weight = options.weight || 0;
            this.show_scale = options.show_scale || false;
            this.next_screen = options.next_screen || false;

            this.click_product_handler = function(event){
                var product = self.pos.db.get_product_by_id(this.dataset['productId']);
                options.click_product_action(product);
            };

            this.product_list = options.product_list || [];
            this.product_cache = new module.DomCache();
        },
        set_product_list: function(product_list){
            this.product_list = product_list;
            this.renderElement();
        },
        get_product_image_url: function(product){
            return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product.id;
        },
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        render_product: function(product){
            var cached = this.product_cache.get_node(product.id);
            if(!cached){
                var image_url = this.get_product_image_url(product);
                var product_html = QWeb.render('Product',{ 
                        widget:  this, 
                        product: product, 
                        image_url: this.get_product_image_url(product),
                    });
                var product_node = document.createElement('div');
                product_node.innerHTML = product_html;
                product_node = product_node.childNodes[1];
                this.product_cache.cache_node(product.id,product_node);
                return product_node;
            }
            return cached;
        },

        renderElement: function() {
            var self = this;

            // this._super()
            var el_str  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;

            var list_container = el_node.querySelector('.product-list');
            for(var i = 0, len = this.product_list.length; i < len; i++){
                var product_node = this.render_product(this.product_list[i]);
                product_node.addEventListener('click',this.click_product_handler);
                list_container.appendChild(product_node);
            };
        },
    });

    /* -------- The Action Buttons -------- */

    // Above the numpad and the actionpad, buttons
    // for extra actions and controls by point of
    // sale extensions modules. 

    module.action_button_classes = [];
    module.define_action_button = function(classe, options){
        options = options || {};

        var classes = module.action_button_classes;
        var index   = classes.length;

        if (options.after) {
            for (var i = 0; i < classes.length; i++) {
                if (classes[i].name === options.after) {
                    index = i + 1;
                }
            }
        } else if (options.before) {
            for (var i = 0; i < classes.length; i++) {
                if (classes[i].name === options.after) {
                    index = i;
                    break;
                }
            }
        }
        classes.splice(i,0,classe);
    };

    module.ActionButtonWidget = module.PosBaseWidget.extend({
        template: 'ActionButtonWidget',
        label: _t('Button'),
        renderElement: function(){
            var self = this;
            this._super();
            this.$el.click(function(){
                self.button_click();
            });
        },
        button_click: function(){},
        highlight: function(highlight){
            this.$el.toggleClass('highlight',!!highlight);
        },
    });

    /* -------- The Product Screen -------- */
    
    module.ProductScreenWidget = module.ScreenWidget.extend({
        template:'ProductScreenWidget',

        start: function(){ 

            var self = this;

            this.actionpad = new module.ActionpadWidget(this,{});
            this.actionpad.replace(this.$('.placeholder-ActionpadWidget'));

            this.numpad = new module.NumpadWidget(this,{});
            this.numpad.replace(this.$('.placeholder-NumpadWidget'));

            this.order_widget = new module.OrderWidget(this,{
                numpad_state: this.numpad.state,
            });
            this.order_widget.replace(this.$('.placeholder-OrderWidget'));

            this.product_list_widget = new module.ProductListWidget(this,{
                click_product_action: function(product){ self.click_product(product); },
                product_list: this.pos.db.get_product_by_category(0)
            });
            this.product_list_widget.replace(this.$('.placeholder-ProductListWidget'));

            this.product_categories_widget = new module.ProductCategoriesWidget(this,{
                product_list_widget: this.product_list_widget,
            });
            this.product_categories_widget.replace(this.$('.placeholder-ProductCategoriesWidget'));

            this.action_buttons = {};
            var classes = module.action_button_classes;
            for (var i = 0; i < classes.length; i++) {
                var classe = classes[i];
                if ( !classe.condition || classe.condition.call(this) ) {
                    var widget = new classe.widget(this,{});
                    widget.appendTo(this.$('.control-buttons'));
                    this.action_buttons[classe.name] = widget;
                }
            }
            if (_.size(this.action_buttons)) {
                this.$('.control-buttons').removeClass('oe_hidden');
            }
        },

        click_product: function(product) {
           if(product.to_weight && this.pos.config.iface_electronic_scale){
               this.gui.show_screen('scale',{product: product});
           }else{
               this.pos.get_order().add_product(product);
           }
        },

        show: function(){
            this._super();
            this.product_categories_widget.reset_category();
            this.numpad.state.reset();
        },

        close: function(){
            this._super();
            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.hide();
            }
        },
    });
    module.Gui.define_screen({name:'products', widget:module.ProductScreenWidget});

    /*--------------------------------------*\
     |         THE CLIENT LIST              |
    \*======================================*/

    // The clientlist displays the list of customer,
    // and allows the cashier to create, edit and assign
    // customers.
    
    module.ClientListScreenWidget = module.ScreenWidget.extend({
        template: 'ClientListScreenWidget',

        init: function(parent, options){
            this._super(parent, options);
            this.partner_cache = new module.DomCache();
        },

        auto_back: true,

        show: function(){
            var self = this;
            this._super();

            this.renderElement();
            this.details_visible = false;
            this.old_client = this.pos.get_order().get_client()
            this.new_client = this.old_client;

            this.$('.back').click(function(){
                self.gui.back();
            });

            this.$('.next').click(function(){   
                self.save_changes();
                self.gui.back();    // FIXME HUH ?
            });

            this.$('.new-customer').click(function(){
                self.display_client_details('edit',{
                    'country_id': self.pos.company.country_id,
                });
            });

            var partners = this.pos.db.get_partners_sorted(1000);
            this.render_list(partners);
            
            this.reload_partners();

            if( this.old_client ){
                this.display_client_details('show',this.old_client,0);
            }

            this.$('.client-list-contents').delegate('.client-line','click',function(event){
                self.line_select(event,$(this),parseInt($(this).data('id')));
            });

            var search_timeout = null;

            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);

                var query = this.value;

                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
        },
        barcode_client_action: function(code){
            if (this.editing_client) {
                this.$('.detail.barcode').val(code.code);
            } else if (this.pos.db.get_partner_by_barcode(code.code)) {
                this.display_client_details('show',this.pos.db.get_partner_by_barcode(code.code));
            }
        },
        perform_search: function(query, associate_result){
            if(query){
                var customers = this.pos.db.search_partner(query);
                this.display_client_details('hide');
                if ( associate_result && customers.length === 1){
                    this.new_client = customers[0];
                    this.save_changes();
                    this.gui.back();
                }
                this.render_list(customers);
            }else{
                var customers = this.pos.db.get_partners_sorted();
                this.render_list(customers);
            }
        },
        clear_search: function(){
            var customers = this.pos.db.get_partners_sorted(1000);
            this.render_list(customers);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
        render_list: function(partners){
            var contents = this.$el[0].querySelector('.client-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(partners.length,1000); i < len; i++){
                var partner    = partners[i];
                var clientline = this.partner_cache.get_node(partner.id);
                if(!clientline){
                    var clientline_html = QWeb.render('ClientLine',{widget: this, partner:partners[i]});
                    var clientline = document.createElement('tbody');
                    clientline.innerHTML = clientline_html;
                    clientline = clientline.childNodes[1];
                    this.partner_cache.cache_node(partner.id,clientline);
                }
                if( partners === this.new_client ){
                    clientline.classList.add('highlight');
                }else{
                    clientline.classList.remove('highlight');
                }
                contents.appendChild(clientline);
            }
        },
        save_changes: function(){
            if( this.has_client_changed() ){
                this.pos.get_order().set_client(this.new_client);
            }
        },
        has_client_changed: function(){
            if( this.old_client && this.new_client ){
                return this.old_client.id !== this.new_client.id;
            }else{
                return !!this.old_client !== !!this.new_client;
            }
        },
        toggle_save_button: function(){
            var $button = this.$('.button.next');
            if (this.editing_client) {
                $button.addClass('oe_hidden');
                return;
            } else if( this.new_client ){
                if( !this.old_client){
                    $button.text(_t('Set Customer'));
                }else{
                    $button.text(_t('Change Customer'));
                }
            }else{
                $button.text(_t('Deselect Customer'));
            }
            $button.toggleClass('oe_hidden',!this.has_client_changed());
        },
        line_select: function(event,$line,id){
            var partner = this.pos.db.get_partner_by_id(id);
            this.$('.client-list .lowlight').removeClass('lowlight');
            if ( $line.hasClass('highlight') ){
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_client_details('hide',partner);
                this.new_client = null;
                this.toggle_save_button();
            }else{
                this.$('.client-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                var y = event.pageY - $line.parent().offset().top
                this.display_client_details('show',partner,y);
                this.new_client = partner;
                this.toggle_save_button();
            }
        },
        partner_icon_url: function(id){
            return '/web/binary/image?model=res.partner&id='+id+'&field=image_small';
        },

        // ui handle for the 'edit selected customer' action
        edit_client_details: function(partner) {
            this.display_client_details('edit',partner);
        },

        // ui handle for the 'cancel customer edit changes' action
        undo_client_details: function(partner) {
            if (!partner.id) {
                this.display_client_details('hide');
            } else {
                this.display_client_details('show',partner);
            }
        },

        // what happens when we save the changes on the client edit form -> we fetch the fields, sanitize them,
        // send them to the backend for update, and call saved_client_details() when the server tells us the
        // save was successfull.
        save_client_details: function(partner) {
            var self = this;
            
            var fields = {}
            this.$('.client-details-contents .detail').each(function(idx,el){
                fields[el.name] = el.value;
            });

            if (!fields.name) {
                this.gui.show_popup('error',_t('A Customer Name Is Required'));
                return;
            }
            
            if (this.uploaded_picture) {
                fields.image = this.uploaded_picture;
            }

            fields.id           = partner.id || false;
            fields.country_id   = fields.country_id || false;
            fields.barcode        = fields.barcode ? this.pos.barcode_reader.sanitize_ean(fields.barcode) : false; 

            new instance.web.Model('res.partner').call('create_from_ui',[fields]).then(function(partner_id){
                self.saved_client_details(partner_id);
            },function(err,event){
                event.preventDefault();
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                    'body': _t('Your Internet connection is probably down.'),
                });
            });
        },
        
        // what happens when we've just pushed modifications for a partner of id partner_id
        saved_client_details: function(partner_id){
            var self = this;
            this.reload_partners().then(function(){
                var partner = self.pos.db.get_partner_by_id(partner_id);
                if (partner) {
                    self.new_client = partner;
                    self.toggle_save_button();
                    self.display_client_details('show',partner);
                } else {
                    // should never happen, because create_from_ui must return the id of the partner it
                    // has created, and reload_partner() must have loaded the newly created partner. 
                    self.display_client_details('hide');
                }
            });
        },

        // resizes an image, keeping the aspect ratio intact,
        // the resize is useful to avoid sending 12Mpixels jpegs
        // over a wireless connection.
        resize_image_to_dataurl: function(img, maxwidth, maxheight, callback){
            img.onload = function(){
                var png = new Image();
                var canvas = document.createElement('canvas');
                var ctx    = canvas.getContext('2d');
                var ratio  = 1;

                if (img.width > maxwidth) {
                    ratio = maxwidth / img.width;
                }
                if (img.height * ratio > maxheight) {
                    ratio = maxheight / img.height;
                }
                var width  = Math.floor(img.width * ratio);
                var height = Math.floor(img.height * ratio);

                canvas.width  = width;
                canvas.height = height;
                ctx.drawImage(img,0,0,width,height);

                var dataurl = canvas.toDataURL();
                callback(dataurl);
            }
        },

        // Loads and resizes a File that contains an image.
        // callback gets a dataurl in case of success.
        load_image_file: function(file, callback){
            var self = this;
            if (!file.type.match(/image.*/)) {
                this.gui.show_popup('error',{
                    title: _t('Unsupported File Format'),
                    body:  _t('Only web-compatible Image formats such as .png or .jpeg are supported'),
                });
                return;
            }
            
            var reader = new FileReader();
            reader.onload = function(event){
                var dataurl = event.target.result;
                var img     = new Image();
                img.src = dataurl;
                self.resize_image_to_dataurl(img,800,600,callback);
            }
            reader.onerror = function(){
                self.gui.show_popup('error',{
                    title :_t('Could Not Read Image'),
                    body  :_t('The provided file could not be read due to an unknown error'),
                });
            };
            reader.readAsDataURL(file);
        },

        // This fetches partner changes on the server, and in case of changes, 
        // rerenders the affected views
        reload_partners: function(){
            var self = this;
            return this.pos.load_new_partners().then(function(){
                self.render_list(self.pos.db.get_partners_sorted(1000));
                
                // update the currently assigned client if it has been changed in db.
                var curr_client = self.pos.get_order().get_client();
                if (curr_client) {
                    self.pos.get_order().set_client(self.pos.db.get_partner_by_id(curr_client.id));
                }
            });
        },

        // Shows,hides or edit the customer details box :
        // visibility: 'show', 'hide' or 'edit'
        // partner:    the partner object to show or edit
        // clickpos:   the height of the click on the list (in pixel), used
        //             to maintain consistent scroll.
        display_client_details: function(visibility,partner,clickpos){
            var self = this;
            var contents = this.$('.client-details-contents');
            var parent   = this.$('.client-list').parent();
            var scroll   = parent.scrollTop();
            var height   = contents.height();

            contents.off('click','.button.edit'); 
            contents.off('click','.button.save'); 
            contents.off('click','.button.undo'); 
            contents.on('click','.button.edit',function(){ self.edit_client_details(partner); });
            contents.on('click','.button.save',function(){ self.save_client_details(partner); });
            contents.on('click','.button.undo',function(){ self.undo_client_details(partner); });
            this.editing_client = false;
            this.uploaded_picture = null;

            if(visibility === 'show'){
                contents.empty();
                contents.append($(QWeb.render('ClientDetails',{widget:this,partner:partner})));

                var new_height   = contents.height();

                if(!this.details_visible){
                    if(clickpos < scroll + new_height + 20 ){
                        parent.scrollTop( clickpos - 20 );
                    }else{
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                }else{
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }

                this.details_visible = true;
                this.toggle_save_button();
            } else if (visibility === 'edit') {
                this.editing_client = true;
                contents.empty();
                contents.append($(QWeb.render('ClientDetailsEdit',{widget:this,partner:partner})));
                this.toggle_save_button();

                contents.find('.image-uploader').on('change',function(){
                    self.load_image_file(event.target.files[0],function(res){
                        if (res) {
                            contents.find('.client-picture img, .client-picture .fa').remove();
                            contents.find('.client-picture').append("<img src='"+res+"'>");
                            contents.find('.detail.picture').remove();
                            self.uploaded_picture = res;
                        }
                    });
                });
            } else if (visibility === 'hide') {
                contents.empty();
                if( height > scroll ){
                    contents.css({height:height+'px'});
                    contents.animate({height:0},400,function(){
                        contents.css({height:''});
                    });
                }else{
                    parent.scrollTop( parent.scrollTop() - height);
                }
                this.details_visible = false;
                this.toggle_save_button();
            }
        },
        close: function(){
            this._super();
        },
    });
    module.Gui.define_screen({name:'clientlist', widget: module.ClientListScreenWidget});

    /*--------------------------------------*\
     |         THE RECEIPT SCREEN           |
    \*======================================*/

    // The receipt screen displays the order's
    // receipt and allows it to be printed in a web browser.
    // The receipt screen is not shown if the point of sale
    // is set up to print with the proxy. Altough it could
    // be useful to do so...

    module.ReceiptScreenWidget = module.ScreenWidget.extend({
        template: 'ReceiptScreenWidget',

        show: function(){
            this._super();
            var self = this;

            this.refresh();

            if (!this.pos.get_order()._printed && this.pos.config.iface_print_auto) {
                this.print();
            }

            // The problem is that in chrome the print() is asynchronous and doesn't
            // execute until all rpc are finished. So it conflicts with the rpc used
            // to send the orders to the backend, and the user is able to go to the next 
            // screen before the printing dialog is opened. The problem is that what's 
            // printed is whatever is in the page when the dialog is opened and not when it's called,
            // and so you end up printing the product list instead of the receipt... 
            //
            // Fixing this would need a re-architecturing
            // of the code to postpone sending of orders after printing.
            //
            // But since the print dialog also blocks the other asynchronous calls, the
            // button enabling in the setTimeout() is blocked until the printing dialog is 
            // closed. But the timeout has to be big enough or else it doesn't work
            // 2 seconds is the same as the default timeout for sending orders and so the dialog
            // should have appeared before the timeout... so yeah that's not ultra reliable. 

            this.lock_screen(true);
            setTimeout(function(){
                self.lock_screen(false);
            }, 2000);
        },
        lock_screen: function(locked) {
            this._locked = locked;
            if (locked) {
                this.$('.next').removeClass('highlight');
            } else {
                this.$('.next').addClass('highlight');
            }
        },
        print: function() {
            this.pos.get_order()._printed = true;
            window.print();
        },
        finish_order: function() {
            if (!this._locked) {
                this.pos.get_order().finalize();
            }
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.next').click(function(){
                self.finish_order();
            });
            this.$('.button.print').click(function(){
                self.print();
            });
        },
        refresh: function() {
            var order = this.pos.get_order();
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                    widget:this,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                }));
        },
    });
    module.Gui.define_screen({name:'receipt', widget:module.ReceiptScreenWidget});

    /*--------------------------------------*\
     |         THE PAYMENT SCREEN           |
    \*======================================*/

    // The Payment Screen handles the payments, and
    // it is unfortunately quite complicated.

    module.PaymentScreenWidget = module.ScreenWidget.extend({
        template:      'PaymentScreenWidget',
        back_screen:   'product',
        next_screen:   'receipt',
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);

            this.pos.bind('change:selectedOrder',function(){
                    this.renderElement();
                    this.watch_order_changes();
                },this);
            this.watch_order_changes();

            this.inputbuffer = "";
            this.firstinput  = true;
            this.keyboard_handler = function(event){
                var key = '';
                if ( event.keyCode === 13 ) {         // Enter
                    self.validate_order();
                } else if ( event.keyCode === 190 ) { // Dot
                    key = '.';
                } else if ( event.keyCode === 46 ) {  // Delete
                    key = 'CLEAR';
                } else if ( event.keyCode === 8 ) {   // Backspace 
                    key = 'BACKSPACE';
                    event.preventDefault(); // Prevents history back nav
                } else if ( event.keyCode >= 48 && event.keyCode <= 57 ){       // Numbers
                    key = '' + (event.keyCode - 48);
                } else if ( event.keyCode >= 96 && event.keyCode <= 105 ){      // Numpad Numbers
                    key = '' + (event.keyCode - 96);
                } else if ( event.keyCode === 189 || event.keyCode === 109 ) {  // Minus
                    key = '-';
                } else if ( event.keyCode === 107 ) { // Plus
                    key = '+';
                }

                self.payment_input(key);

            };
        },
        // resets the current input buffer
        reset_input: function(){
            var line = this.pos.get_order().selected_paymentline;
            this.firstinput  = true;
            if (line) {
                this.inputbuffer = this.format_currency_no_symbol(line.get_amount());
            } else {
                this.inputbuffer = "";
            }
        },
        // handle both keyboard and numpad input. Accepts
        // a string that represents the key pressed.
        payment_input: function(input) {
            var oldbuf = this.inputbuffer.slice(0);
            var newbuf = this.gui.numpad_input(this.inputbuffer, input, {'firstinput': this.firstinput});

            this.firstinput = (newbuf.length === 0);

            // popup block inputs to prevent sneak editing. 
            if (this.gui.has_popup()) {
                return;
            }
            
            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                var order = this.pos.get_order();
                if (order.selected_paymentline) {
                    order.selected_paymentline.set_amount(parseFloat(this.inputbuffer));
                    this.order_changes();
                    this.render_paymentlines();
                    this.$('.paymentline.selected .edit').text(this.inputbuffer);
                }
            }
        },
        click_numpad: function(button) {
            this.payment_input(button.data('action'));
        },
        render_numpad: function() {
            var self = this;
            var numpad = $(QWeb.render('PaymentScreen-Numpad', { widget:this }));
            numpad.on('click','button',function(){
                self.click_numpad($(this));
            });
            return numpad;
        },
        click_delete_paymentline: function(cid){
            var lines = this.pos.get_order().get_paymentlines();
            for ( var i = 0; i < lines.length; i++ ) {
                if (lines[i].cid === cid) {
                    this.pos.get_order().remove_paymentline(lines[i]);
                    this.reset_input();
                    this.render_paymentlines();
                    return;
                }
            }
        },
        click_paymentline: function(cid){
            var lines = this.pos.get_order().get_paymentlines();
            for ( var i = 0; i < lines.length; i++ ) {
                if (lines[i].cid === cid) {
                    this.pos.get_order().select_paymentline(lines[i]);
                    this.reset_input();
                    this.render_paymentlines();
                    return;
                }
            }
        },
        render_paymentlines: function() {
            var self  = this;
            var order = this.pos.get_order();
            if (!order) {
                return;
            }

            var lines = order.get_paymentlines();

            this.$('.paymentlines-container').empty();
            var lines = $(QWeb.render('PaymentScreen-Paymentlines', { 
                widget: this, 
                order: order,
                paymentlines: lines,
            }));

            lines.on('click','.delete-button',function(){
                self.click_delete_paymentline($(this).data('cid'));
            });

            lines.on('click','.paymentline',function(){
                self.click_paymentline($(this).data('cid'));
            });
                
            lines.appendTo(this.$('.paymentlines-container'));
        },
        click_paymentmethods: function(id) {
            var cashregister = null;
            for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
                if ( this.pos.cashregisters[i].journal_id[0] === id ){
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            this.pos.get_order().add_paymentline( cashregister );
            this.reset_input();
            this.render_paymentlines();
        },
        render_paymentmethods: function() {
            var self = this;
            var methods = $(QWeb.render('PaymentScreen-Paymentmethods', { widget:this }));
                methods.on('click','.paymentmethod',function(){
                    self.click_paymentmethods($(this).data('id'));
                });
            return methods;
        },
        click_invoice: function(){
            var order = this.pos.get_order();
            order.set_to_invoice(!order.is_to_invoice());
            if (order.is_to_invoice()) {
                this.$('.js_invoice').addClass('highlight');
            } else {
                this.$('.js_invoice').removeClass('highlight');
            }
        },
        click_set_customer: function(){
            this.gui.show_screen('clientlist');
        },
        click_back: function(){
            this.gui.show_screen('products');
        },
        renderElement: function() {
            var self = this;
            this._super();

            var numpad = this.render_numpad();
            numpad.appendTo(this.$('.payment-numpad'));

            var methods = this.render_paymentmethods();
            methods.appendTo(this.$('.paymentmethods-container'));

            this.render_paymentlines();

            this.$('.back').click(function(){
                self.click_back();
            });

            this.$('.next').click(function(){
                self.validate_order();
            });

            this.$('.js_set_customer').click(function(){
                self.click_set_customer();
            });
            this.$('.js_invoice').click(function(){
                self.click_invoice();
            });

            this.$('.js_cashdrawer').click(function(){
                self.pos.proxy.open_cashbox();
            });

        },
        show: function(){
            this.pos.get_order().clean_empty_paymentlines();
            this.reset_input();
            this.render_paymentlines();
            this.order_changes();
            window.document.body.addEventListener('keydown',this.keyboard_handler);
            this._super();
        },
        hide: function(){
            window.document.body.removeEventListener('keydown',this.keyboard_handler);
            this._super();
        },
        // sets up listeners to watch for order changes
        watch_order_changes: function() {
            var self = this;
            var order = this.pos.get_order();
            if (!order) {
                return;
            }
            if(this.old_order){
                this.old_order.unbind(null,null,this);
            }
            order.bind('all',function(){
                self.order_changes();
            });
            this.old_order = order;
        },
        // called when the order is changed, used to show if
        // the order is paid or not
        order_changes: function(){
            var self = this;
            var order = this.pos.get_order();
            if (!order) {
                return;
            } else if (order.is_paid()) {
                self.$('.next').addClass('highlight');
            }else{
                self.$('.next').removeClass('highlight');
            }
        },
        print_escpos_receipt: function(){
            var env = {
                widget:  this,
                pos:     this.pos,
                order:   this.pos.get_order(),
                receipt: this.pos.get_order().export_for_printing(),
            };

            this.pos.proxy.print_receipt(QWeb.render('XmlReceipt',env));
        },

        // Check if the order is paid, then sends it to the backend,
        // and complete the sale process
        validate_order: function(force_validation) {
            var self = this;

            var order = this.pos.get_order();

            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Order'),
                    'body':  _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = order.get_paymentlines();
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }

            if (!order.is_paid() || this.invoicing) {
                return;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error',{
                        title: _t('Cannot return change without a cash payment method'),
                        body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm',{
                    title: _t('Please Confirm Large Amount'),
                    body:  _t('Are you sure that the customer wants to  pay') + 
                           ' ' + 
                           this.format_currency(order.get_total_paid()) +
                           ' ' +
                           _t('for an order of') +
                           ' ' +
                           this.format_currency(order.get_total_with_tax()) +
                           ' ' +
                           _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function() {
                        self.validate_order('confirm');
                    },
                });
                return;
            }

            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) { 

                    this.pos.proxy.open_cashbox();
            }

            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;

                invoiced.fail(function(error){
                    self.invoicing = false;
                    if (error === 'error-no-client') {
                        self.gui.show_popup('confirm',{
                            'title': _t('Please select the Customer'),
                            'body': _t('You need to select the customer before you can invoice an order.'),
                            confirm: function(){
                                self.gui.show_screen('clientlist');
                            },
                        });
                    } else {
                        self.gui.show_popup('error',{
                            'title': _t('The order could not be sent'),
                            'body': _t('Check your internet connection and try again.'),
                        });
                    }
                });

                invoiced.done(function(){
                    self.invoicing = false;
                    order.finalize();
                });
            } else {
                this.pos.push_order(order) 
                if (this.pos.config.iface_print_via_proxy) {
                    this.print_escpos_receipt();
                    order.finalize();    //finish order and go back to scan screen
                } else {
                    this.gui.show_screen(this.next_screen);
                }
            }
        },
    });
    module.Gui.define_screen({name:'payment', widget:module.PaymentScreenWidget});

};

