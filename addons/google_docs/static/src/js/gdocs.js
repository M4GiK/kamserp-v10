openerp.google_docs = function(instance, m) {
var _t = instance.web._t,
    QWeb = instance.web.qweb;

    instance.web.Sidebar.include({
    	
    	start: function() {
            var self = this;
            var ids 
            this._super.apply(this, arguments);
            var view = self.getParent();
            var result;
            if(view.fields_view.type == "form"){
            	ids = []
            	view.on("load_record", self, function(r){
		            	ids = [r.id]
		            	self.add_gdoc_items(view,ids)
            		});
            	}
        	},
        
	      add_gdoc_items: function(view,ids){
	        	var self = this;
	        	var gdoc_item = _.indexOf(_.pluck(self.items.other,'classname'),'oe_share_gdoc');
	        	if(gdoc_item !== -1)
	        	{
	        		self.items.other.splice(gdoc_item,1);
	        	}
	        	if( !_.isEmpty(ids) ){
	                view.sidebar_eval_context().done(function (context) {
		            var ds = new instance.web.DataSet(this, 'ir.attachment', context);
		            ds.call('google_doc_get', [view.dataset.model, ids, context]).done(function(r) {
		            	if(!_.isEmpty(r)){
		            	_.each(r,function(res){
		            		var g_item = _.indexOf(_.pluck(self.items.other,'label'),res);
				        	if(g_item !== -1)
				        	{
				        		self.items.other.splice(g_item,1);
				        	}
				   
		            		self.add_items('other', [
		                    {   label: res,
		                        callback: self.on_google_doc,
		                        classname: 'oe_share_gdoc' },
		                	]);
		            	  })
		               }
		              });
		            });
		         }
	        },
        
        
	        on_google_doc: function(r) {
	            var self = this;
	            var view = self.getParent();
	            var ids = ( view.fields_view.type != "form" )? view.groups.get_selection().ids : [ view.datarecord.id ];
	            if( !_.isEmpty(ids) ){
	                view.sidebar_eval_context().done(function (context) {
	                    var ds = new instance.web.DataSet(this, 'ir.attachment', context);
	                    ds.call('get_attachment', [view.dataset.model, r, ids, context]).done(function(res) {
	                        window.open(res.url,"_blank");
	                        view.reload();
	                    })
	                    	
	                });
	            }
	        }
    });
};
