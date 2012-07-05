/*---------------------------------------------------------
 * OpenERP web_graph
 *---------------------------------------------------------*/

openerp.web_graph = function (instance) {

var _lt = instance.web._lt;

// removed ``undefined`` values
var filter_values = function (o) {
    var out = {};
    for (var k in o) {
        if (!o.hasOwnProperty(k) || o[k] === undefined) { continue; }
        out[k] = o[k];
    }
    return out;
};

instance.web.views.add('graph', 'instance.web_graph.GraphView');
instance.web_graph.GraphView = instance.web.View.extend({
    template: "GraphView",
    display_name: _lt('Graph'),
    view_type: "graph",

    init: function(parent, dataset, view_id, options) {
        this._super(parent);
        this.set_default_options(options);
        this.dataset = dataset;
        this.view_id = view_id;

        this.mode = "bar";          // line, bar, area, pie, radar
        this.orientation = false;    // true: horizontal, false: vertical
        this.stacked = true;

        this.spreadsheet = false;   // Display data grid, allows copy to CSV
        this.forcehtml = false;
        this.legend = "top";        // top, inside, no

        this.domain = [];
        this.context = {};
        this.group_by = [];

        this.graph = null;
    },
    destroy: function () {
        if (this.graph) {
            this.graph.destroy();
        }
        this._super();
    },

    on_loaded: function(fields_view_get) {
        // TODO: move  to load_view and document
        var self = this;
        this.fields_view = fields_view_get;
        this.$element.addClass(this.fields_view.arch.attrs['class']);

        this.mode = this.fields_view.arch.attrs.type || 'bar';
        this.orientation = this.fields_view.arch.attrs.orientation == 'horizontal';

        var width = this.$element.parent().width();
        this.$element.css("width", width);
        this.container = this.$element.find("#editor-render-body").css({
            width: width,
            height: Math.min(500, width * 0.8)
        })[0];

        var graph_render = this.proxy('graph_render');
        this.$element.on('click', '.oe_graph_options a', function (evt) {
            var $el = $(evt.target);

            self.graph_render({data: filter_values({
                mode: $el.data('mode'),
                legend: $el.data('legend'),
                orientation: $el.data('orientation'),
                stacked: $el.data('stacked')
            })});
        });

        this.$element.find("#graph_show_data").click(function () {
            self.spreadsheet = ! self.spreadsheet;
            self.graph_render();
        });
        this.$element.find("#graph_switch").click(function () {
            if (self.mode != 'radar') {
                self.orientation = ! self.orientation;
            }
            self.graph_render();
        });

        this.$element.find("#graph_download").click(function () {
            if (self.legend == "top") { self.legend = "inside"; }
            self.forcehtml = true;

            self.graph_get_data().then(function (result) {
                self.graph_render_all(result).download.saveImage('png');
            }).always(function () {
                self.forcehtml = false;
            });
        });
        return this._super();
    },

    get_format: function (options) {
        options = options || {};
        var legend = {
            show: this.legend != 'no',
        };

        switch (this.legend) {
        case 'top':
            legend.noColumns = 4;
            legend.container = this.$element.find("div.graph_header_legend")[0];
            break;
        case 'inside':
            legend.position = 'nw';
            legend.backgroundColor = '#D2E8FF';
            break;
        }

        return _.extend({
            legend: legend,
            mouse: {
                track: true,
                relative: true
            },
            spreadsheet : {
                show: this.spreadsheet,
                initialTab: "data"
            },
            HtmlText : (options.xaxis && options.xaxis.labelsAngle) ? false : !this.forcehtml,
        }, options);
    },

    make_graph: function (mode, container, data) {
        if (mode === 'area') { mode = 'line'; }
        return Flotr.draw(
            container, data.data,
            this.get_format(this['options_' + mode](data)));
    },

    options_bar: function (data) {
        var min = _(data.data).chain()
            .map(function (record) {
                return _.min(record.data, function (item) {
                    return item[1];
                })[1];
            }).min().value();
        return {
            bars : {
                show : true,
                stacked : this.stacked,
                horizontal : this.orientation,
                barWidth : 0.7,
                lineWidth : 1
            },
            grid : {
                verticalLines : this.orientation,
                horizontalLines : !this.orientation,
                outline : "sw",
            },
            yaxis : {
                ticks: this.orientation ? data.ticks : false,
                min: !this.orientation ? (min < 0 ? min : 0) : null
            },
            xaxis : {
                labelsAngle: 45,
                ticks: this.orientation ? false : data.ticks,
                min: this.orientation ? (min < 0 ? min : 0) : null
            }
        };
    },

    options_pie: function (data) {
        return {
            pie : {
                show: true
            },
            grid : {
                verticalLines : false,
                horizontalLines : false,
                outline : "",
            },
            xaxis :  {showLabels: false},
            yaxis :  {showLabels: false},
        };
    },

    options_radar: function (data) {
        return {
            radar : {
                show : true,
                stacked : this.stacked
            },
            grid : {
                circular : true,
                minorHorizontalLines : true
            },
            xaxis : {
                ticks: data.ticks
            },
        };
    },

    options_line: function (data) {
        return {
            lines : {
                show : true,
                stacked : this.stacked
            },
            grid : {
                verticalLines : this.orientation,
                horizontalLines : !this.orientation,
                outline : "sw",
            },
            yaxis : {
                ticks: this.orientation ? data.ticks : false
            },
            xaxis : {
                labelsAngle: 45,
                ticks: this.orientation ? false : data.ticks
            }
        };
    },

    graph_get_data: function () {
        return this.rpc('/web_graph/graph/data_get', {
            model: this.dataset.model,
            domain: this.domain,
            context: this.context,
            group_by: this.group_by,
            view_id: this.view_id,
            mode: this.mode,
            orientation: this.orientation,
            stacked: this.stacked
        });
    },

    // Render the graph and update menu styles
    graph_render: function (options) {
        options = options || {};
        _.extend(this, options.data);

        return this.graph_get_data()
            .then(this.proxy('graph_render_all'));
    },

    graph_render_all: function (data) {
        var i;
        if (this.mode=='area') {
            for (i=0; i<data.data.length; i++) {
                data.data[i].lines = {fill: true}
            }
        }
        if (this.graph) {
            this.graph.destroy();
        }

        // Render the graph
        this.$element.find(".graph_header_legend").children().remove();
        this.graph = this.make_graph(this.mode, this.container, data);

        // Update styles of menus

        this.$element.find("a").removeClass("active");

        var $active = this.$element.find('a[data-mode=' + this.mode + ']');
        if ($active.length > 1) {
            $active = $active.filter('[data-stacked=' + this.stacked + ']');
        }
        $active = $active.add(
            this.$element.find('a:not([data-mode])[data-legend=' + this.legend + ']'));

        $active.addClass('active');

        if (this.spreadsheet) {
            this.$element.find("#graph_show_data").addClass("active");
        }
        return this.graph;
    },

    // render the graph using the domain, context and group_by
    // calls the 'graph_data_get' python controller to process all data
    // TODO: check is group_by should better be in the context
    do_search: function(domain, context, group_by) {
        this.domain = domain;
        this.context = context;
        this.group_by = group_by;

        this.graph_render();
    },

    do_show: function() {
        this.do_push_state({});
        return this._super();
    },
});
};
