Ext.onReady(function() {
    Ext.QuickTips.init();
 
	var statusrecord = Ext.data.Record.create([
       {name: 'cpus'},
       {name: 'dbusy'},
       {name: 'didle'},
       {name: 'dpending'},
       {name: 'ebusy'},
       {name: 'eidle'},
       {name: 'epending'},
       {name: 'job'},
       {name: 'load'},
       {name: 'memtot'},
       {name: 'memused'},
       {name: 'role'},
       {name: 'privateip'},
       {name: 'publicip'},
       {name: 'queue'},
       {name: 'status'},
       {name: 'type'},
       {name: 'uptime'},
    ]);

	var pipelinerecord = Ext.data.Record.create([
            {name: 'pipelineid'},
            {name: 'state'},
            {name: 'componenttype'},
            {name: 'componentname'},
            {name: 'xml'},
            {name: 'commandcount'},
            {name: 'osize'},
            {name: 'repository'},
            {name: 'runtime'},
            {name: 'lastmod'}
	]);

    var workflowrecord = Ext.data.Record.create([
            {name: 'seconds'},
            {name: 'id'},
            {name: 'name'},
            {name: 'executable'},
            {name: 'state'},
            {name: 'startTime'},
            {name: 'endTime'},
            {name: 'runtime'},
            {name: 'fileName'},
            {name: 'executionHost'},
            {name: 'gridID'},
    ]);



	var countsdata = new Array(Ext.v_maxnodes);
	for (y=0; y<Ext.v_maxnodes; y++) {
		countsdata[y] = [y+' instances',y];  
	}
    var countsstore = new Ext.data.SimpleStore({
                    fields: ['name', 'count'],
                    data : countsdata 
    });
	
	var typesdata = [ ['exec','exec'],['data','data'] ];
    var typesstore = new Ext.data.SimpleStore({
            fields: ['name', 'desc'],
            data : typesdata
    });


	var countbox = new Ext.form.ComboBox({
                                            tpl: '<tpl for="."><div ext:qtip="{name}" class="x-combo-list-item">{count}</div></tpl>',
                                            store: countsstore,
                                            mode: 'local',
                                            forceSelection: true,
                                            fieldLabel: "Number",
										    triggerAction: 'all',
    										selectOnFocus:true,
											name:'count',
											displayField: 'count',
											valueField: 'count',
                                            emptyText:Ext.v_execr+' exec, '+Ext.v_datar+' data running'
                                      });

	var countboxhandler = function(record){
		launchbutton.setText("Launch "+countbox.getValue()+" instances");
		launchbutton.setDisabled(false);
	}
	countbox.on('select',countboxhandler,this);

	var launchform =  new Ext.FormPanel({
        url:'launch.cgi',
        frame:true,
        bodyStyle:'padding:5px 5px 0',
        width: 400,
        defaults: {width: 400},
        items: [
               countbox,
				{
                xtype: 'radiogroup',
                fieldLabel: 'Role',
			 	itemCls: 'x-check-group-alt',
                columns: 2,
                vertical: true,
                items: [
                {boxLabel: 'Data', name: 'node-role', inputValue: 'data'},
                {boxLabel: 'Exec', name: 'node-role', inputValue: 'exec', checked: true},
               ]},
               {
                xtype: 'radiogroup',
                fieldLabel: 'Type',
                itemCls: 'x-check-group-alt',
                columns: 2,
                vertical: true,
                items: [
                {boxLabel: 'small', name: 'node-type', inputValue: 'm1.small', checked: true},
                {boxLabel: 'medium', name: 'node-type', inputValue: 'c1.medium'},
               ]}
              ]
	});
	
	var launchbutton = new Ext.Button({ text : 'Launch',disabled : true, 
										handler : function (){
										launchform.getForm().submit({url:'launch.cgi', waitMsg:'Launching instances...'});
										launchbutton.setText("Launch");
								        launchbutton.setDisabled(false);
										win.hide();
										}});	
	//launch window
	var win = new Ext.Window({
                applyTo     : 'launch-win',
                layout      : 'fit',
                width       : 550,
                height      : 210,
                closeAction :'hide',
          		items: launchform, 
                buttons: [launchbutton,{text : 'Cancel',handler : function(){ win.hide();}}]
            });
 	
	function launchDialog(scope, options){
			win.show();
        };
   

	Ext.v_statusstore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: 'gridinfo.cgi'}),
            reader: new Ext.data.JsonReader({},statusrecord),
         //   data: Ext.v_statustable,
            sortInfo:{field: 'privateip', direction: "ASC"},
            groupField:'role'
        });

    Ext.v_pipelinestore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: 'pipelineinfo.cgi'}),
            reader: new Ext.data.JsonReader({},pipelinerecord),
         //   data: Ext.v_statustable,
            sortInfo:{field: 'pipelineid', direction: "ASC"},
            groupField:'componenttype'
        });

	Ext.v_showwfxml = function(xml) {
		Ext.wftabxml = xml;
        Ext.v_workflowstore.proxy = new Ext.data.HttpProxy({url: 'workflowinfo.cgi?xml='+Ext.wftabxml});
		loadWorkflow();
	    tabs.setActiveTab('workflowstatustab');
    }


	Ext.v_workflowstore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: 'workflowinfo.cgi?xml='+Ext.wftabxml}),
            reader: new Ext.data.JsonReader({},workflowrecord),
         //   data: Ext.v_statustable,
            sortInfo:{field: 'seconds', direction: "DESC"},
            groupField:'name'
        });

    var tabs = new Ext.TabPanel({
        renderTo:'dashboard',
        resizeTabs:true, // turn on tab resizing
        minTabWidth: 115,
        tabWidth:135,
        enableTabScroll:true,
        width:1001,
        height:400,
        defaults: {autoScroll:true},
    });

    function addGridStatusTab(){
        tabs.add({
            title: 'Grid Status',
            iconCls: 'tabs',
            html: '<div id="gprogress"></div><div id="gridstatus"></div>',
            closable:false,
			id: 'gridstatustab',
// inline toolbars
        tbar:[{
            text:'Launch new nodes',
            tooltip:Ext.v_datar+' data,'+Ext.v_execr+' exec running',
            iconCls:'add',
            id:'dolaunchbutton',
            handler: launchDialog
        }, '-',{text:'Update',handler: loadGrid}]
        }).show();
    }


	function loadPipeline(){
	Ext.v_pipelinestore.load();
    Ext.v_pbar = new Ext.ProgressBar({renderTo: 'pprogress',height: 10});
    Ext.v_pbar.show();
    Ext.v_pbar.wait();
    Ext.v_pipelinestore.on('load', function(){Ext.v_pbar.reset();Ext.v_pbar.hide()});
	}

    function loadGrid(){
    Ext.v_statusstore.load();
    Ext.v_gbar = new Ext.ProgressBar({renderTo: 'gprogress',height: 10});
    Ext.v_gbar.show();
    Ext.v_gbar.wait();
    Ext.v_statusstore.on('load', function(){Ext.v_gbar.reset();Ext.v_gbar.hide()});
    }


	function loadWorkflow(){
    Ext.v_workflowstore.load();
    Ext.v_wbar = new Ext.ProgressBar({renderTo: 'wprogress',height: 10});
    Ext.v_wbar.show();
    Ext.v_wbar.wait();
    Ext.v_workflowstore.on('load', function(){Ext.v_wbar.reset();Ext.v_wbar.hide()});
    }


    function addPipelineTab(){
        tabs.add({
            title: 'Pipeline Summary',
            iconCls: 'tabs',
			id: 'pipelinestatustab',
            html: '<div id="pprogress"></div><div id="pipelinestatus"></div>',
            closable:false,
			tbar:[{text:'Update',handler: loadPipeline}]
        }).show();
    }

	function addWorkflowTab(){
        tabs.add({
            title: 'Workflow',
            iconCls: 'tabs',
			id: 'workflowstatustab',
            html: '<div id="wprogress"></div><div id="workflowstatus"></div>',
            closable:false,
			tbar:[{text:'Update',handler: loadWorkflow}]
        }).show();
    }	


	addGridStatusTab();
	addPipelineTab();
	addWorkflowTab();
 	tabs.setActiveTab('gridstatustab');

	var pipelinegrid = new Ext.grid.EditorGridPanel({
        frame:true,
        width: 1000,
        height: 450,
        collapsible: true,
        animCollapse: true,
        iconCls: 'icon-grid',
        renderTo: 'pipelinestatus',

        store: Ext.v_pipelinestore,

       cm: new Ext.grid.ColumnModel([
            {header: "pipeline id", width: 60, sortable: true, dataIndex: 'pipelineid'},
            {header: "state", width: 60, sortable: true, dataIndex: 'state'},
            {header: "SOP", width: 60, sortable: true, dataIndex: 'pipelineid'},
            {header: "name", width: 60, sortable: true, dataIndex: 'componentname'},
            {header: "type", width: 60, sortable: true, dataIndex: 'componenttype'},
            {header: "xml", width: 60, sortable: true, dataIndex: 'xml'},
            {header: "# commands", width: 60, sortable: true, dataIndex: 'commandcount'},
            {header: "output size", width: 60, sortable: true, dataIndex: 'osize'},
            {header: "repository", width: 60, sortable: true, dataIndex: 'repository'},
            {header: "runtime", width: 60, sortable: true, dataIndex: 'runtime'},
            {header: "lastmod", width: 60, sortable: true, dataIndex: 'lastmod'}
			]),
        view: new Ext.grid.GroupingView({
			groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]})',
            forceFit:true
        }),
    });

	Ext.sum = function (a){
        var s=0;
        for(var i=0;i<a.length;i++){
            s = s+parseInt(a[i].data["seconds"]);
        }
        return s;
    }

	Ext.sumhrs = function (a){
        var s=0;
        for(var i=0;i<a.length;i++){
            s = s+parseInt(a[i].data["seconds"]);
        }
        s = s/60/60;
		return s.toFixed(2);
    }


    Ext.avg = function (a){
		var avg= Ext.sum(a)/a.length;
		return avg.toFixed(1);
	}

	Ext.stddev = function (a){
		var v=0;
		var avg = Ext.avg(a);
		for(var i=0;i<a.length;i++){
            v = v+Math.pow(parseInt(a[i].data["seconds"])-avg,2);
        }
		return Math.sqrt(v/a.length).toFixed(1);
	}

    var worklfowgrid = new Ext.grid.EditorGridPanel({
        frame:true,
        width: 1000,
        height: 350,
        collapsible: true,
        animCollapse: true,
        iconCls: 'icon-grid',
        renderTo: 'workflowstatus',

        store: Ext.v_workflowstore,

       cm: new Ext.grid.ColumnModel([
            {header: "seconds", width: 60, sortable: true, dataIndex: 'seconds'},
            {header: "name", width: 60, sortable: true, dataIndex: 'name'},
            {header: "executable", width: 60, sortable: true, dataIndex: 'executable'},
            {header: "state", width: 60, sortable: true, dataIndex: 'state'},
            {header: "startTime", width: 60, sortable: true, dataIndex: 'startTime'},
            {header: "endTime", width: 60, sortable: true, dataIndex: 'endTime'},
            {header: "runtime", width: 60, sortable: true, dataIndex: 'runtime'},
//            {header: "file", width: 60, sortable: true, dataIndex: 'filename'},
            {header: "host", width: 60, sortable: true, dataIndex: 'executionHost'},
            {header: "SGE id", width: 60, sortable: true, dataIndex: 'gridID'}
            ]),
        view: new Ext.grid.GroupingView({
			groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]}) Avg:{[Ext.avg(values.rs)]}s+/-{[Ext.stddev(values.rs)]} Total:{[Ext.sumhrs(values.rs)]} CPU hrs',
            forceFit:true
        }),
    });

	
	var gridstatusgrid = new Ext.grid.EditorGridPanel({
		frame:true,
        width: 1000,
        height: 350,
        collapsible: true,
        animCollapse: true,
//        title: 'Vappio launchpad for Grid V1',
        iconCls: 'icon-grid',
        renderTo: 'gridstatus',

        store: Ext.v_statusstore,
 
       cm: new Ext.grid.ColumnModel([
            {id:'publicip',header: "Public IP", width: 60, sortable: true, dataIndex: 'publicip',
            editor: new Ext.form.TextField({
             allowBlank: false
            })},
            {header: "Private IP", width: 60, sortable: true, dataIndex: 'privateip',editor: new Ext.form.TextField({
             allowBlank: false
            })},
            {header: "role", width: 20, sortable: true, dataIndex: 'role',
			editor: new Ext.form.ComboBox({
			  transform: roles,
			  triggerAction: 'all',
			  lazyRender: true,
			  typeAhead: true,
              listClass: 'x-combo-list-small'
			})},
            {header: "type", width: 30, sortable: true, dataIndex: 'type'},
            {header: "status", width: 30, sortable: true, dataIndex: 'status'},
            {header: "idle data", width: 20, sortable: true, dataIndex: 'didle'},
            {header: "busy data", width: 20, sortable: true, dataIndex: 'dbusy'},
            {header: "pending data", width: 20, sortable: true, dataIndex: 'ppending'},
            {header: "idle exec", width: 20, sortable: true, dataIndex: 'eidle'},
            {header: "busy exec", width: 20, sortable: true, dataIndex: 'ebusy'},
            {header: "pending exec", width: 20, sortable: true, dataIndex: 'epending'},
            {header: "load", width: 20, sortable: true, dataIndex: 'load'},
            {header: "memused", width: 20, sortable: true, dataIndex: 'memused'},
            {header: "uptime", width: 20, sortable: true, dataIndex: 'uptime'}
		]),
        view: new Ext.grid.GroupingView({
            forceFit:true,
            groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Types" : "Type"]})'
        }),
// inline buttons
//     buttons: [{text:'Save'},{text:'Cancel'}],
//     buttonAlign:'center',
    });

loadGrid();
loadPipeline();
calcnodes();
});

Ext.v_maxnodes = 100;
Ext.v_datar = 0;
Ext.v_execr = 0;
function calcnodes(){
    var roles = Ext.v_statusstore.collect('role');
	//Ext.v_datar;
	//Ext.v_execr;
	for (x in roles){
		if(roles[x] == 'data'){
			Ext.v_datar = Ext.v_datar + 1;
		}
		if(roles[x] == 'exec'){
			Ext.v_execr = Ext.v_execr + 1;
		}
	}
	Ext.v_availnodes = Ext.v_maxnodes - Ext.v_datar - Ext.v_execr;

//	alert(Ext.v_availnodes);
    Ext.v_countsdata = new Array(Ext.v_availnodes);
    for (y=0; y<Ext.v_maxnodes; y++) {
        Ext.v_countsdata[y] = [y+' instances',y];
    }
    Ext.v_countsstore = new Ext.data.SimpleStore({
                    fields: ['name', 'count'],
                    data : Ext.v_countsdata
    });
//   causes error 
//   Ext.get('dolaunchbutton').setText('Launch nodes ('+Ext.v_datar+' data,'+Ext.v_execr+' exec running)');
}



