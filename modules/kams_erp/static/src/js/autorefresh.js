odoo.define('kams_erp.autorefresh', function (require) {
"use strict";

	instance.web.ListView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){
					if(this.$el[0].clientWidth != 0){
						this.reload();
					}
				}, self), parent.action.auto_refresh*1000);
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });

	instance.web.FormView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){
					if(this.$el[0].clientWidth != 0 && this.dataset.index != null){
						this.reload();
					}
				}, self), parent.action.auto_refresh*1000);
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
});