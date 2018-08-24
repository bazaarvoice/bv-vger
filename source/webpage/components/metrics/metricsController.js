/*
 *  Controller for the metrics page
 *  Handles input forms and rendering google chart
 */

(function(){
    'use strict';

    angular.module('vgerMetricsController', [])
    .controller('metricsController', metricsController);

    metricsController.$inject = ['$scope', '$q', '$location', '$controller', '$rootScope', '$window',
        '$mdDialog', 'metricsFilterService', 'metricsDataService', 'dateService', 'constantsService', 'googleChartApiPromise', '$mdToast'];
    function metricsController($scope, $q, $location, $controller, $rootScope, $window,
                               $mdDialog, metricsFilterService, metricsDataService, dateService, constantsService, googleChartApiPromise, $mdToast) {
        var vm = this; // view-model
        
        vm.teams = [];
        vm.projects = [];
        vm.workTypes = [];
        vm.selectedTeam = {};
        vm.selectedProject = {};
        vm.selectedWorkTypes = [];
        vm.graphError = vm.showTags = vm.submitted = vm.workTypeError = vm.editingWorkTypes = vm.editingWorkStates = vm.editingProject = vm.serverError = false;
        vm.throughputGraph = vm.velocityGraph = {};
        vm.leadTimeTrends, vm.leadTimePercentile, vm.leadTimeMode;
        vm.throughputGraphBuilt = vm.velocityGraphBuilt = vm.leadTimeGraphBuilt = vm.predictabilityGraphBuilt = false;
        vm.viewMode = "issue";

        vm.filter = filter;
        vm.hideTPSeries = hideTPSeries;
        vm.hideLTSeries = hideLTSeries;
        vm.changePercentileCurve = changePercentileCurve;
        vm.toggleGitTags = toggleGitTags;
        vm.leadTimePercentileChange = leadTimePercentileChange;
        vm.changeVelocityCurve = changeVelocityCurve;
        vm.showLeadTimeTrends = showLeadTimeTrends;
        vm.leadTimeModeChange = leadTimeModeChange;
        vm.projectSettingsModal = projectSettingsModal;
        vm.openMenu = openMenu;
        vm.getBoardID = getBoardID;
        vm.addWebpageConstants = addWebpageConstants;
        vm.updateWebpageConstants = updateWebpageConstants;
        vm.buildNewURL = buildNewURL;
        vm.changeSelectedWorkTypes = changeSelectedWorkTypes;
        vm.workStatesSettingsModal = workStatesSettingsModal;
        vm.workTypesSettingsModal = workTypesSettingsModal;
        vm.viewModeChange= viewModeChange;
        vm.downloadThroughput = downloadThroughput;
        vm.projectETL = projectETL;
        vm.issueTypeETL = issueTypeETL;
        vm.hasGitRepo = false;
        vm.hasGitTag = false;
        vm.hamburgerMenuOpened = false;
        vm.errorStatus;
        vm.searchDateSince;
        vm.searchDateUntil;
        vm.searchDays;
        vm.fileName = "";

        var dateSince, dateUntil, days;
        var isPointsStraight = false;
        var curvedDataPoints = [], straightDataPoints = [];
        var throughputData = [], velocityData = [], predictabilityData = [], leadTimeData = {}, gitData = {};
        var throughputTickets = [];
        var absoluteBacklogHistory = [], relativeBacklogHistory = [];
        var backlogSeries = [];
        var leadTimeStages = [];
        var throughputLabels = [], velocityLabels = [], predictabilityLabels = [], leadTimeLabels = [];

        // Open project settings when first redirected from creating a new team project
        var newTeamProject = $location.search().newTeamProject;
        if (newTeamProject) {
            vm.projectSettingsModal();
        }

        // Save scope between configuration and metrics page
        getSessionScope();
        getWorkTypes(filter);

        //initial function calls needed to build quarterly reports URL info
        getBoardID();

        function getSessionScope() {
            // Check bookmarked query params
            var queryParams = $location.search();
            vm.selectedTeam.id = queryParams['teamId'];
            vm.selectedProject.id = queryParams['projectId'];
            vm.selectedTeam.name = queryParams['teamName'];
            vm.selectedProject.name = queryParams['projectName'];

            if (vm.selectedProject.id && !$window.sessionStorage.selectedProjectId) {
                $rootScope.selectedTeamId = vm.selectedTeam.id;
                $rootScope.selectedTeamName = vm.selectedTeam.name;
                $window.sessionStorage.selectedTeamId = vm.selectedTeam.id;
                $window.sessionStorage.selectedTeamName = vm.selectedTeam.name;
                $rootScope.selectedProjectId = vm.selectedProject.id;
                $rootScope.selectedProjectName = vm.selectedProject.name;
                $window.sessionStorage.selectedProjectId = vm.selectedProject.id;
                $window.sessionStorage.selectedProjectName = vm.selectedProject.name;
            } else if (!vm.selectedProject.id && $window.sessionStorage.selectedProjectId) {
                // console.log('Searched');
                vm.selectedTeam.id = $window.sessionStorage.selectedTeamId;
                vm.selectedProject.id = $window.sessionStorage.selectedProjectId;
                vm.selectedTeam.name = $window.sessionStorage.selectedTeamName;
                vm.selectedProject.name = $window.sessionStorage.selectedProjectName;
            }
        }

        // Get list of work types for the project
        function getWorkTypes(callback) {
            var promiseWorkType = metricsFilterService.getWorkTypes(vm.selectedProject.id);
            promiseWorkType.then(function(response) {
                vm.workTypes = [];                                           // Initialize with empty list on each new call
                vm.selectedWorkTypesModel = [];
                vm.selectedWorkTypes = [];
                vm.workTypeError = false;
                // Iterating through each dictionary key and saving the values into workTypes & selectedWorkTypes array
                // All work types are selected initially; append all to selectedWorkTypes
                var count = 1;
                var worktype = {};

                Object.keys(response.data).sort(function (a, b) {
                    return a.toLowerCase().localeCompare(b.toLowerCase());
                }).map(function(key) {
                    // template for angularjs-dropdown-multiselect
                    worktype = {
                        'id': count,
                        'label' : key
                    }
                    vm.workTypes.push(worktype);
                    vm.selectedWorkTypesModel.push(worktype);
                    vm.selectedWorkTypes.push(key);
                    count ++;
                });

                if (typeof(callback) === "function" && callback) {
                    callback();
                }

            }).catch(function(errorResponse) {
            // console.log(errorResponse);
            })
        }

        vm.dropdownSettings = {
            showCheckAll: true,
            showUncheckAll: true
        };

        // TODO can't read from controller-as syntax; using $scope for now; might be a bug in the ng-dropdown-multiselect library
        $scope.dropdownEvents = {
            workTypes: {
                onSelectionChanged: function () {
                    getSelectedWorkTypes();
                }
            },
        }

        function getSelectedWorkTypes() {
            vm.selectedWorkTypes = []; // Clear past selection
            for (var index in vm.selectedWorkTypesModel) {
                vm.selectedWorkTypes.push(vm.selectedWorkTypesModel[index].label);
            }
            if (vm.selectedWorkTypes.length <= 0) {
                vm.workTypeError = true;
            } else {
                vm.workTypeError = false;
            }
        }

        // Invoked by Submit button
        function filter() {
            dateSince =  dateService.getDateSince();
            dateUntil = dateService.getDateUntil();
            days = dateService.getDays();
            
            if (!dateUntil) {
                dateUntil = new Date();
                dateService.setDateUntil(dateUntil);
            }
            if (!dateSince) {
                dateSince = new Date();
                dateSince.setDate(dateUntil.getDate()-90);
                dateService.setDateSince(dateSince);
            }
            
            vm.searchDateSince = dateSince;
            vm.searchDateUntil = dateUntil;
            vm.searchDays = dateService.getDays();

            $location.search({
                teamId : vm.selectedTeam.id,
                projectId : vm.selectedProject.id,
                teamName : vm.selectedTeam.name,
                projectName: vm.selectedProject.name,
                to: formatDate(vm.searchDateUntil),
                from: formatDate(vm.searchDateSince),
                workTypes: (vm.selectedWorkTypes.join())
            });

            (vm.viewMode == 'issue') ? updateMetrics() : updatePRMetrics();
        }

        function errorHandler(errorResponse, caller) {
            caller = caller || 'default';
            if (caller == 'gitRepo' || caller == 'gitTag') {
                // TODO: handle with alert message, show tooltip on disabled button
                // Git repository or git tag is optional
                vm.hasGitRepo = false;
                vm.hasGitTag = false;
                return;
            } else if (caller != 'default') {
                console.log(errorResponse);
                vm.graphError = true;
            } else {
                console.log(errorResponse);
                vm.serverError = true;
            }
            return $q.reject(errorResponse);
        }


        function warningToast(message) {
            var el = angular.element(document.querySelector('#metricsToastController'));
            $mdToast.show(
                $mdToast.simple()
                    .textContent(message)
                    .action('OK')
                    .position('top right')
                    .hideDelay(5000)
            );
        }

        // TODO use dateController
        function formatDate(date) {
            var d = new Date(date),
                month = '' + (d.getMonth() + 1),
                day = '' + d.getDate(),
                year = d.getFullYear();
            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;
            return [year, month, day].join('-');
        }

        function buildThroughputGraph() {
            // console.log('buildThroughputGraph');
            var deferred = $.Deferred();
            var dateLabels = [];
            for (var date in throughputLabels){
                var newDate = new Date(throughputLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var y_axis_label = (vm.viewMode == "issue") ? 'Issues Completed' : 'PRs Completed';
            var chart = {
                type: 'LineChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    height: '100%',
                    legend: { position: 'top' },
                    vAxis: {
                        title: y_axis_label,
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        viewWindow: {
                            min: 0
                        },
                        minValue: 0
                    },
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    curveType: 'function',
                    colors: ['#000', '#CCCCCC', '#006400', '#808000' , '#cc8400'],
                    defaultColors: ['#000', '#CCCCCC', '#006400', '#808000' , '#cc8400'],
                    series: {
                        0: { lineWidth: 3 , pointShape: 'circle', pointSize: 7 },
                        1: { lineWidth: 0 , pointSize: 0 },
                        2: { lineWidth: 1 , pointShape: 'triangle', pointSize: 10 },
                        3: { lineWidth: 1 , pointShape: 'square', pointSize: 10 },
                        4: { lineWidth: 1 , pointShape: 'diamond', pointSize: 10 },
                    },
                    annotations: {
                        style: 'line'
                    },
                    focusTarget: 'category'
                }
            }

            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags) {
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            var sorted = [];
            for(var key in throughputData) {
                sorted[sorted.length] = key;
            }
            sorted.sort().reverse();
            for (var col in sorted) {
                data.addColumn('number', sorted[col]);
                if (sorted[col] === 'Actual') {
                    data.addColumn('number', 'Likeliness');
                }
            }
            for (var week in throughputLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags){
                    row.push(null);
                    row.push(null);
                }
                for (var series in sorted) {
                    key=sorted[series];
                    row.push(throughputData[key][week]);
                    if (sorted[series] === 'Actual') {
                        row.push(null);
                    }
                }
                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in  gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key)) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            row.push(null);
                            row.push(null);
                            row.push(null);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
                chart.view = {
                    columns: Array.from(Array(chart.options.colors.length + 3).keys())
                };
            } else {
                chart.view = {
                    columns: Array.from(Array(chart.options.colors.length + 1).keys())
                };
            }
            chart.data = data;
            vm.throughputGraph = chart;
            vm.throughputGraphBuilt = true;
            // console.log('buildThroughputGraph done');
            return deferred.promise();
        }

        function buildVelocityGraph(){
            // console.log('buildVelocityGraph');
            var deferred = $.Deferred();
            var dateLabels = [];
             for (var date in velocityLabels) {
                var newDate = new Date(velocityLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'AreaChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    height: '100%',
                    legend: { position: 'top' },
                    vAxis: {
                        title: 'Number of Issues',
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        format: 'short'
                    },
                    areaOpacity: 0.1,
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    curveType: 'function',
                    pointSize: 5,
                    series: {
                        0: { lineWidth: 1, pointShape: 'circle'},
                        1: { lineWidth: 1, pointShape: 'triangle' },
                    },
                    annotations: {
                        style: 'line'
                    },
                    focusTarget: 'category'
                }
            }

            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags) {
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            for (var col in backlogSeries) {
                data.addColumn('number', backlogSeries[col]);
            }
            for (var week in velocityLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags) {
                    row.push(null);
                    row.push(null);
                }
                row.push(velocityData[0][week]);
                row.push(velocityData[1][week]);

                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in  gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key) && key > velocityLabels[0]) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
            }
            chart.data = data;
            vm.velocityGraph = chart;
            vm.velocityGraphBuilt = true;
            // console.log ('buildVelocityGraph done');
            return deferred.promise();
        }

        function buildPRVelocityGraph() {
            // console.log('buildVelocityGraph');
            var deferred = $.Deferred();
            var dateLabels = [];
             for (var date in velocityLabels) {
                var newDate = new Date(velocityLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'AreaChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    height: '100%',
                    legend: { position: 'top' },
                    vAxis: {
                        title: 'Total Volume (Lines)',
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        format: 'short'
                    },
                    areaOpacity: 0.1,
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    pointSize: 5,
                    series: {
                        0: {lineWidth: 1, pointShape: 'circle', color: "red"},
                        1: {lineWidth: 1, pointShape: 'triangle', color: "blue"}
                    },
                    annotations: {
                        style: 'line'
                    },
                    isStacked: true,
                    focusTarget: 'category'
                }
            }

            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags) {
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            // Rejected Volume should be first
            for (var col in backlogSeries.sort().reverse()) {
                data.addColumn('number', backlogSeries[col]);
            }
            for (var week in velocityLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags) {
                    row.push(null);
                    row.push(null);
                }
                // Rejected Volume should be first
                row.push(velocityData[1][week]);
                row.push(velocityData[0][week]);
                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in  gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key) && key > velocityLabels[0]) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
            }
            chart.data = data;
            vm.velocityGraph = chart;
            vm.velocityGraphBuilt = true;
            // console.log ('buildVelocityGraph done');
            return deferred.promise();
        }

        function buildPredictabilityGraph() {
            // console.log('buildPredictabilityGraph');
            var deferred = $.Deferred();
            var dateLabels = [];
            for (var date in predictabilityLabels){
                var newDate = new Date(predictabilityLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'LineChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    height: '100%',
                    legend: { position: 'none' },
                    vAxis: {
                        title: 'Predictability (lower variation is better)',
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        viewWindow: {
                            min: 0
                        },
                        minValue: 0
                    },
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    curveType: 'function',
                    pointSize: 5,
                    colors: ['black'],
                    series: {
                        0: { lineWidth: 1 }
                    },
                    annotations: {
                        style: 'line'
                    },
                    focusTarget: 'category'
                }
            }
            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags){
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            data.addColumn('number', 'CoV');
            for (var week in predictabilityLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags) {
                    row.push(null);
                    row.push(null);
                }
                row.push(predictabilityData[week]);
                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key) && key > predictabilityLabels[0]) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
            }
            chart.data = data;
            vm.predictabilityGraph = chart;
            vm.predictabilityGraphBuilt = true;
            // console.log ('buildPredictabilityGraph done');
            return deferred.promise();
        }

        function buildOverallLeadTimeGraph() {
            // console.log('buildOverallLeadTimeGraph');
            var deferred = $.Deferred();
            var dateLabels = [];
            for (var date in leadTimeLabels) {
                var newDate = new Date(leadTimeLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'LineChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    legend: { position: 'top' },
                    vAxis: {
                        title: 'Working Days',
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        viewWindow: {
                            min: 0
                        },
                        minValue: 0
                    },
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    annotations: {
                        style: 'line'
                    },
                    colors: ['#CC0000','#0000FF', '#DD9900'],
                    defaultColors:['#CC0000','#0000FF', '#DD9900'],
                    curveType: 'function',
                    pointSize: 5,
                    series: {
                        0: { lineWidth: 1 , pointShape: 'triangle', pointSize: 10 },
                        1: { lineWidth: 1 , pointShape: 'star', pointSize: 10 },
                        2: { lineWidth: 1 , pointShape: 'diamond', pointSize: 10 }
                    },
                    focusTarget: 'category'
                }
            }
            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags) {
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            var sorted = [];
            for(var key in leadTimeData) {
                sorted[sorted.length] = key;
            }
            sorted.sort().reverse();
            for (var col in sorted) {
                data.addColumn('number', sorted[col]);
            }

            for (var week in leadTimeLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags){
                    row.push(null);
                    row.push(null);
                }
                for (var series in sorted) {
                    key=sorted[series];
                    row.push(leadTimeData[key][0][week]);
                }
                data.addRow(row);
            }

            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in  gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key) && key > leadTimeLabels[0]) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            row.push(null);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
                chart.view = {
                    columns: Array.from(Array(Object.keys(chart.options.series).length + 3).keys())
                };
            } else {
                chart.view = {
                    columns: Array.from(Array(Object.keys(chart.options.series).length + 1).keys())
                };
            }
            chart.data = data;
            vm.leadTimeGraph = chart;
            vm.leadTimeGraphBuilt = true;
            // console.log ('buildOverallLeadTimeGraph done');
            return deferred.promise();
        }

        function buildDetailedLeadTimeGraph() {
            var dateLabels = [];
            for (var date in leadTimeLabels) {
                var newDate = new Date(leadTimeLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'ColumnChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%'
                    },
                    legend: { position: 'top' },
                    vAxis: {
                        title: 'Lifespan of issue (Working Days)',
                        titleTextStyle: {
                            italic: false
                        },
                        viewWindow: {
                            min: 0
                        },
                        gridlines: {},
                        minValue: 0
                        },
                        annotations: {
                            style: 'line'
                        },
                        hAxis: {
                            title: 'Weeks',
                            titleTextStyle: {
                              italic: false
                          },
                          format: 'M/d/yy',
                          ticks: dateLabels,
                          gridlines: {}
                        },
                    colors: ['black', '#e2431e', '#f1ca3a', '#6f9654', '#1c91c0',
                     '#4374e0', '#5c3292', '#572a1a', '#999999', '#1a1a1a'],
                    defaultColors: ['black', '#e2431e', '#f1ca3a', '#6f9654', '#1c91c0',
                     '#4374e0', '#5c3292', '#572a1a', '#999999', '#1a1a1a'],
                    curveType: 'function',
                    seriesType: 'bars',
                }
            }
            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags){
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            var newSeries = {};
            var colourIndex = 0;
            for (var col in leadTimeStages) {
                console.log('var col in leadTimeStages');
                console.log(col);
                if (leadTimeStages[col] === 'Overall') {
                    // replace overall title with percentile title
                    newSeries[Object.keys(newSeries).length] = {type: 'line', pointSize: 4};
                    data.addColumn('number', vm.leadTimePercentile + ' Overall');
                } else {
                    if (vm.leadTimeTrends){
                        newSeries[Object.keys(newSeries).length] = {type: 'line', pointSize: 4};
                    } else {
                        newSeries[Object.keys(newSeries).length] = {type: 'bar'};
                    }
                    data.addColumn('number', leadTimeStages[col]);
                }
                colourIndex+=1;
            }
            chart.options.series = newSeries;
            for (var week in leadTimeLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags) {
                    row.push(null);
                    row.push(null);
                }
                for (var series in leadTimeStages) {
                    row.push(leadTimeData[vm.leadTimePercentile][series][week]);
                }
                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key) && key > leadTimeLabels[0]) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                        for (var series in leadTimeStages) {
                            row.push(null);
                        }
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
                chart.view = { columns: Array.from(Array(Object.keys(newSeries).length + 3).keys()) };
            } else {
                chart.view = { columns: Array.from(Array(Object.keys(newSeries).length + 1).keys()) };
            }
            chart.data = data;
            vm.leadTimeGraph = chart;
            vm.leadTimeGraphBuilt = true;
        }

        function buildPRLeadTimeGraph() {
            var dateLabels = [];
            var deferred = $.Deferred();
            for (var date in leadTimeLabels) {
                var newDate = new Date(leadTimeLabels[date]);
                newDate.setDate(newDate.getDate());
                dateLabels.push(newDate);
            }
            var chart = {
                type: 'LineChart',
                options: {
                    chartArea:{
                        width: '90%',
                        height: '80%',
                        left: '7%',
                        top: '7%'
                    },
                    legend: { position: 'top' },
                    vAxis: {
                        title: 'Working Days',
                        titleTextStyle: {
                            italic: false
                        },
                        gridlines: {},
                        viewWindow: {
                            min: 0
                        },
                        minValue: 0
                    },
                    hAxis: {
                        title: 'Weeks',
                        titleTextStyle: {
                            italic: false
                        },
                        format: 'M/d/yy',
                        ticks: dateLabels,
                        gridlines:{
                        }
                    },
                    annotations: {
                        style: 'line'
                    },
                    colors: ['#CC0000','#0000FF', '#DD9900'],
                    defaultColors:['#CC0000','#0000FF', '#DD9900'],
                    curveType: 'function',
                    pointSize: 5,
                    series: {
                        0: { lineWidth: 1 , pointShape: 'triangle', pointSize: 10 },
                        1: { lineWidth: 1 , pointShape: 'star', pointSize: 10 },
                        2: { lineWidth: 1 , pointShape: 'diamond', pointSize: 10 }
                    },
                    focusTarget: 'category'
                }
            };
            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Week');
            if (vm.showTags) {
                data.addColumn({type: 'string', role: 'annotation'});
                data.addColumn({type: 'string', role: 'tooltip'});
            }
            var sorted = [];
            for(var key in leadTimeData) {
                sorted[sorted.length] = key;
            }
            sorted.sort().reverse();
            for (var col in sorted) {
                data.addColumn('number', sorted[col]);
            }
            for (var week in leadTimeLabels) {
                var row = [];
                row.push(dateLabels[week]);
                if (vm.showTags){
                    row.push(null);
                    row.push(null);
                }
                for (var series in sorted) {
                    key=sorted[series];
                    row.push(leadTimeData[key][week]);
                }
                data.addRow(row);
            }
            if (vm.showTags) {
                for (var repo in gitData) {
                    for (var key in  gitData[repo]) {
                        var row = [];
                        if (gitData[repo].hasOwnProperty(key)) {
                            row.push(new Date(key));
                            row.push('');
                            row.push(gitData[repo][key]);
                            row.push(null);
                            row.push(null);
                            row.push(null);
                            data.addRow(row);
                        }
                    }
                }
                chart.options.vAxis.gridlines.color = 'transparent';
                chart.options.hAxis.gridlines.color = 'transparent';
                chart.view = {
                    columns: Array.from(Array(chart.options.colors.length + 3).keys())
                };
            } else {
                chart.view = {
                    columns: Array.from(Array(chart.options.colors.length + 1).keys())
                };
            }
            vm.leadTimeGraph = chart;
            vm.leadTimeGraphBuilt = true;
            chart.data = data;
            return deferred.promise();
        }

        function hideTPSeries(selectedItem) {
            var col = selectedItem.column;
            if (selectedItem.row === null) {
                if (vm.throughputGraph.view.columns[col] == col) {
                    vm.throughputGraph.view.columns[col] = {
                        label: vm.throughputGraph.data.Mf[col].label,
                        type: vm.throughputGraph.data.Mf[col].type,
                        calc: function() {
                            return null;
                        }
                    };
                    vm.throughputGraph.options.colors[col - 1] = '#CCCCCC';
                }
                else {
                    vm.throughputGraph.view.columns[col] = col;
                    vm.throughputGraph.options.colors[col - 1] = vm.throughputGraph.options.defaultColors[col - 1];
                }
            }
        }

        function hideLTSeries(selectedItem) {
            var col = selectedItem.column;
            if (selectedItem.row === null) {
                if (vm.leadTimeGraph.view.columns[col] == col) {
                    vm.leadTimeGraph.view.columns[col] = {
                        label: vm.leadTimeGraph.data.Mf[col].label,
                        type: vm.leadTimeGraph.data.Mf[col].type,
                        calc: function() {
                            return null;
                        }
                    };
                    vm.leadTimeGraph.options.colors[col - 1] = '#CCCCCC';
                }
                else {
                    vm.leadTimeGraph.view.columns[col] = col;
                    vm.leadTimeGraph.options.colors[col - 1] = vm.leadTimeGraph.options.defaultColors[col - 1];
                }
            }
        }

        function changePercentileCurve() {
            isPointsStraight = !isPointsStraight;
            if (isPointsStraight == true) {
                for (var key in straightDataPoints) {
                    throughputData[key] = straightDataPoints[key];
                }
            } else {
                for (var key in curvedDataPoints) {
                    throughputData[key] = curvedDataPoints[key];
                }
            }
            googleChartApiPromise.then(buildThroughputGraph);
        }

        function toggleGitTags() {
            if (!vm.hasGitRepo) {
                warningToast("No Github repos are defined for this project.\n");
                return
            }
            if (!vm.hasGitTag) {
                warningToast("No tags can be found in current time period with current repo.\n");
                return
            }
            buildThroughputGraph();
            buildPredictabilityGraph();
            if (vm.viewMode == "issue") {
                buildVelocityGraph();
                (vm.leadTimeMode == 'overall') ? buildOverallLeadTimeGraph() : buildDetailedLeadTimeGraph();
            } else {
                buildPRVelocityGraph();
                buildPRLeadTimeGraph();
            }
        }

        function leadTimePercentileChange() {
            buildDetailedLeadTimeGraph();
        }

        function changeVelocityCurve() {
            velocityData = (vm.velocityRelative == false) ? absoluteBacklogHistory : relativeBacklogHistory;
            buildVelocityGraph();
        }

        function showLeadTimeTrends() {
            buildDetailedLeadTimeGraph();
        }

        function leadTimeModeChange() {
            (vm.leadTimeMode == 'overall') ? buildOverallLeadTimeGraph() : buildDetailedLeadTimeGraph();
        }

        function viewModeChange() {
            if (vm.viewMode == 'issue') {
                console.log("Issue View");
                updateWebpageConstants();
                updateMetrics();
            } else {
                if (Object.keys(gitData).length === 0) {
                    warningToast("No Github repos are defined for this project.\n");
                    vm.viewMode = 'issue';
                    return
                }
                console.log("Pull requests view");
                updateWebpageConstants();
                updatePRMetrics();
            }
        }

        function downloadThroughput() {
            vm.fileName = vm.selectedProject.name + "_" + vm.viewMode + "_" +
                formatDate(vm.searchDateSince) + "-" + formatDate(vm.searchDateUntil);

            var output = throughputLabels.map(function(e, i) {
              return [e.slice(0, 10), throughputData["Actual"][i], throughputTickets[i]];
            });
            return output;
        }

        function projectETL() {
            var projectETLPromise = metricsDataService.projectETL(vm.selectedProject.id, false);
            projectETLPromise.then(function(response) {
                warningToast("Successfully triggered ETL for " + vm.selectedProject.name + ". Please come back later when data gets loaded.");
            }).catch(function(errorResponse) {
                warningToast(errorResponse.data)
            })
        }

        function issueTypeETL() {
            var issueTypeETlPromise = metricsDataService.projectETL(vm.selectedProject.id, true);
            issueTypeETlPromise.then(function(response) {
                warningToast("Successfully triggered issue type ETL.");
                setTimeout(function() {
                    window.location.reload()
                }, 2500)
            }).catch(function(errorResponse) {
                warningToast(errorResponse.data)
            })
        }
        
        function workStatesSettingsModal(ev) {
            vm.editingWorkStates = true;
            $mdDialog.show({
              controller: DialogController,
              templateUrl: 'components/configurations/editWorkStates.html',
              parent: angular.element(document.body),
              targetEvent: ev,
              clickOutsideToClose:true,
              fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
            })
            .then(function() {
              // on success
              vm.editingWorkStates = false;
          }, function() {
              // on cancel
              vm.editingWorkStates = false;
          });
        }
        
        function workTypesSettingsModal(ev) {
            vm.editingWorkTypes = true;
            $mdDialog.show({
              controller: DialogController,
              templateUrl: 'components/configurations/editWorkTypes.html',
              parent: angular.element(document.body),
              targetEvent: ev,
              clickOutsideToClose:true,
              fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
            })
            .then(function() {
              // on success
              vm.editingWorkTypes = false;
              getWorkTypes();
            }, function() {
              // on cancel
              vm.editingWorkTypes = false;
            });
        }
        
        function projectSettingsModal(ev) {
            vm.editingProject = true;
            $mdDialog.show({
              controller: DialogController,
              templateUrl: 'components/configurations/editProject.html',
              parent: angular.element(document.body),
              targetEvent: ev,
              clickOutsideToClose:true,
              fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
            })
            .then(function() {
              // on success
              vm.editingProject = false;
            }, function() {
              // on cancel
              vm.editingProject = false;
            });
        }

        //helper function to build new URL based on current URL parameters
        function buildNewURL(){
            var currURL = window.location.href;
            var URLQueryParams = currURL.split("&");
            //remove first part of URL that contains root address, so that just the params remain 
            var initLink = URLQueryParams[0].split("?")[0].replace('metrics','reports');
            URLQueryParams[0] = URLQueryParams[0].split("?")[1];

            var newURLString = "";

            for (var i=0; i < URLQueryParams.length; i++){
                if(URLQueryParams[i].includes("teamId") || URLQueryParams[i].includes("projectId") || 
                    URLQueryParams[i].includes("teamName") || URLQueryParams[i].includes("projectName") || 
                    URLQueryParams[i].includes("workTypes")){
                    if(newURLString == "")
                        newURLString += "?" + URLQueryParams[i];
                    else
                        newURLString += "&" + URLQueryParams[i];
                }
            }

            //add any elements from sessionStorage as well
            if($window.sessionStorage.selectedBoardID != null)
                newURLString += "&boardID=" + $window.sessionStorage.selectedBoardID;      


            //SHOULD BE LAST PART OF URL STRING
            //add selected work types as well
            newURLString += "&selectedWorkTypes="+vm.selectedWorkTypes.join(',');
            
            //store in sessionStorage to add to new URL later
            sessionStorage.setItem('newURLString', newURLString)
            var linkDOM = document.getElementById("reports-Link");
            var link = initLink + newURLString;
            linkDOM.setAttribute("href", link);
        }

        function changeSelectedWorkTypes(){
            //get initial link
            var linkDOM = document.getElementById("reports-Link");
            var link = linkDOM.href;

            //remove current selectedworktypes
            var newURL = link.split("&selectedWorkTypes=")[0];

            //get new selected
            var workTypesArrLength = Object.keys(vm.selectedWorkTypesModel).length;
            var selectedWorkTypesString = ""
            for(var i=0; i<workTypesArrLength;i++){
                if(i==workTypesArrLength-1)
                    selectedWorkTypesString += encodeURIComponent(vm.selectedWorkTypesModel[i].label);
                else
                    selectedWorkTypesString += encodeURIComponent(vm.selectedWorkTypesModel[i].label) + ",";
            }

            //append new worktypes to url
            newURL += "&selectedWorkTypes=" + selectedWorkTypesString;
            linkDOM.setAttribute("href", newURL);            
        }

        function openMenu(){
            $('.mainNavDropDown').slideToggle(500);
            var body = window.$("body");
            setTimeout(function(){ 
                if(vm.hamburgerMenuOpened){ 
                    vm.hamburgerMenuOpened = false;
                    body.removeClass("hamburgerOpened");
                }
                else{
                    vm.hamburgerMenuOpened = true;
                    body.addClass("hamburgerOpened")
                }
            }, 600);
        }

        function getBoardID(){
            var promiseJiraIssueConfiguration = metricsDataService.getJiraIssueConfiguration(vm.selectedProject.id);
            promiseJiraIssueConfiguration.then(function(responseBoard) {
                var boardIDPromise = metricsDataService.getBoardID(responseBoard["data"]["boardName"]);
                boardIDPromise.then(function(responseID) {
                    $window.sessionStorage.selectedBoardID= responseID["data"]["board_id"];
                    var linkDOM = document.getElementById("JIRA-Link");
                    var link = $rootScope.BOARD_ID_URL + responseID["data"]['board_id'];
                    linkDOM.setAttribute("href", link);
                    buildNewURL();
                });
            });
            addWebpageConstants();
        }

        function addWebpageConstants() {
            if(!$rootScope.VGER_GUIDE){
                constantsService.setRootScopeConstants();
            }

            var link = document.getElementById("vger_guide_link")
            link.href = $rootScope.VGER_GUIDE;

            link = document.getElementById("jira_support_project_url");
            link.href = $rootScope.JIRA_SUPPORT_PROJECT_URL;

            link = document.getElementById("jira_support_project_url2");
            link.href = $rootScope.JIRA_SUPPORT_PROJECT_URL;

            link = document.getElementById("quadrant_1_link");
            link.href = $rootScope.THROUGHPUT_README;

            link = document.getElementById("jira_support_project_url3");
            link.href = $rootScope.JIRA_SUPPORT_PROJECT_URL;

            link = document.getElementById("jira_support_project_url4");
            link.href = $rootScope.JIRA_SUPPORT_PROJECT_URL;

            link = document.getElementById("quadrant_3_link");
            link.href = $rootScope.THROUGHPUT_VARIATION_README;

            link = document.getElementById("jira_support_project_url5");
            link.href = $rootScope.JIRA_SUPPORT_PROJECT_URL;

            link = document.getElementById("quadrant_4_link")
            link.href = $rootScope.LEADTIMES_README;


        }

        function updateWebpageConstants() {
            if(vm.viewMode == 'issue'){
                var link = document.getElementById("quadrant_2_link");
                link.href = $rootScope.BACKLOG_README;
            }
            else{
                var link = document.getElementById("quadrant_2_link");
                link.href = $rootScope.PR_GROWTH_README;
            }
        }
        
        function DialogController($scope, $mdDialog) {
            $scope.hide = function() {
                $mdDialog.hide();
            };

            $scope.cancel = function() {
                $mdDialog.cancel();
            };
        }

        function updatePRMetrics() {
            vm.throughputGraphBuilt = false;
            vm.velocityGraphBuilt = false;
            vm.predictabilityGraphBuilt = false;
            vm.leadTimeGraphBuilt = false;
            vm.submitted = true;
            vm.graphError = false;
            vm.workTypeError = false;

            dateSince = formatDate(vm.searchDateSince);
            dateUntil = formatDate(vm.searchDateUntil);

            var repoNameList = Object.keys(gitData);

            var prHistoryPromise = metricsDataService.getPRHistoryData(repoNameList,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var prStatisticsPromise = metricsDataService.getPRStatisticsData(repoNameList,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var prPredictabilityPromise = metricsDataService.getPRPredictabilityData(repoNameList,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var prLeadtimePromise = metricsDataService.getPRLeadtimeData(repoNameList,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var prBacklogPromise = metricsDataService.getPRBacklogData(repoNameList,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var throughputGitTagPromise = metricsDataService.getThroughputGitTagData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);

            throughputGitTagPromise.then(function(response) {
                for (var repo in response.data) {
                    var tags = response.data[repo];
                    for (var tag in tags) {
                        var date = response.data[repo][tag][0];
                        var tagName = response.data[repo][tag][1];
                        gitData[repo][date] = tagName;
                    }
                    if (tags.length > 0) {
                        vm.hasGitTag = true;
                    }
                }
                // Build Throughput Graph
                // ================== START prHistoryPromise  =============================
                prHistoryPromise.then(function(response) {
                    straightDataPoints = [];

                    throughputLabels = [];
                    var dataPoints = [];
                    for (var tuple in response.data) {
                        var indexString = response.data[tuple][0];
                        if(indexString.includes("Straight")){
                            console.log("made it")
                            if(indexString == "ninetiethStraight" || indexString == "eightiethStraight")
                                continue;
                            else{
                                if (indexString == 'tenthStraight') {
                                    indexString = '90%';
                                } else if (indexString == 'twentiethStraight') {
                                    indexString = '80%';
                                } else if (indexString == 'fiftiethStraight') {
                                    indexString = '50%';
                                }
                                straightDataPoints[indexString] = response.data[tuple][1];
                            }
                        }
                        else
                            dataPoints.push(response.data[tuple][1]);
                    }
                    throughputData['Actual'] = dataPoints;

                    prStatisticsPromise.then(function(response) {
                        for (var key in response.data) {
                            var insertKey = '';
                            if (key == 'ninetieth') {
                                continue;
                            } else if (key == 'eightieth') {
                                continue;
                            } else if (key == 'fiftieth') {
                                insertKey = '50%';
                            } else if (key == 'twentieth') {
                                insertKey = '80%';
                            } else if (key == 'tenth') {
                                insertKey = '90%';
                            }
                            var weeks = response.data[key];
                            var dataPoints = [];
                            for (var week in weeks) {
                                dataPoints.push(weeks[week][1]);
                            }
                            curvedDataPoints[insertKey] = dataPoints;
                        }
                        var weeks = response.data[Object.keys(response.data)[0]];
                        for (var week in weeks) {
                            throughputLabels.push(weeks[week][0]);
                        }

                        for (var key in curvedDataPoints) {
                            throughputData[key] = curvedDataPoints[key];
                        }
                        googleChartApiPromise.then(buildThroughputGraph) // <---
                    });
                }).catch(function(errorResponse) {
                    errorHandler(errorResponse, 'throughput');
                });
                // ================== END prHistoryPromise  ===============================

                // Build Predictability Graph
                // ================== START predictabilityPromise  ==========================
                prPredictabilityPromise.then(function(response) {
                    predictabilityLabels = [];
                    var dataPoints = [];
                    for (var week in response.data) {
                        predictabilityLabels.push(response.data[week][0]);
                        dataPoints.push(response.data[week][1]);
                    }
                    predictabilityData = dataPoints;
                    googleChartApiPromise.then(buildPredictabilityGraph); // <---
                }).catch(function(errorResponse) {
                    errorHandler(errorResponse, 'predictability');
                });
                // ================== END predictabilityPromise  ==========================

                // Build Leadtime Graph
                // ================== START leadTimePromise ==========================
                prLeadtimePromise.then(function(response) {
                    leadTimeLabels = [];
                    // console.log('leadTimePromise returned ', response.status, ' with response data: ', response.data);
                    for (var key in response.data) {
                        var weeks = response.data[key];
                        var insertKey = '';
                        if (key == 'ninetieth'){
                            insertKey = '90%';
                        } else if (key == 'eightieth') {
                            insertKey = '80%';
                        } else if (key == 'fiftieth') {
                            insertKey = '50%';
                        }
                        var tmpLabels = [];
                        var dataPoints = [];
                        for (var week in weeks) {
                            tmpLabels.push(weeks[week][0]);
                            dataPoints.push(weeks[week][1]);
                        }
                        if (leadTimeLabels.length < 1){
                            leadTimeLabels = (tmpLabels);
                        }

                        leadTimeData[insertKey] = dataPoints;
                    }

                    googleChartApiPromise.then(buildPRLeadTimeGraph); // <---

                }).catch(function(errorResponse) {
                    errorHandler(errorResponse, 'leadtime');
                });
                // ================== END leadTimePromise ==========================

                // Build Backlog Graph
                // ================== START backlogPromise =========================
                prBacklogPromise.then(function(response) {
                    velocityLabels = [];
                    velocityData = [];
                    backlogSeries = [];
                    for (var key in response.data) {
                        var weeks = response.data[key];
                        var dataPoints = [];
                        for (var week in weeks) {
                            if (week == 0) {
                                continue;
                            }
                            dataPoints.push(weeks[week][1]);
                        }
                        backlogSeries.push(key);
                        velocityData.push(dataPoints);
                    }
                    var weeks = response.data[Object.keys(response.data)[0]];
                    for (var week in weeks) {
                        velocityLabels.push(weeks[week][0]);
                    }
                    // From API it's using start of week as week label so slicing the label make it shifted 1 week later
                    // which is exactly what UI wants: use end of week as label.
                    // Also since the current week has not ended yet so last value get ignored
                    velocityLabels = velocityLabels.slice(1,velocityLabels.length);
                    googleChartApiPromise.then(buildPRVelocityGraph); // <---
                }).catch(function(errorResponse) {
                    errorHandler(errorResponse, 'velocity');
                });
                // ================== END backlogPromise ===========================
            });

        }



        function updateMetrics() {
            vm.throughputGraphBuilt = false;
            vm.velocityGraphBuilt = false;
            vm.predictabilityGraphBuilt = false;
            vm.leadTimeGraphBuilt = false;
            vm.submitted = true;
            vm.graphError = false;
            vm.workTypeError = false;
            vm.viewMode = 'issue';
            throughputLabels = [], velocityLabels = [], predictabilityLabels = [], leadTimeLabels = [];

            dateSince = formatDate(vm.searchDateSince);
            dateUntil = formatDate(vm.searchDateUntil);

            // All Graphs Promises
            var throughputGitRepoPromise = metricsDataService.getThroughputGitRepoData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var throughputGitTagPromise = metricsDataService.getThroughputGitTagData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            
            // Throughput Graph Promises
            var throughputStatisticsPromise = metricsDataService.getThroughputStatisticsData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);
            var throughputHistoryPromise = metricsDataService.getThroughputHistoryData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);

            // Velocity Graph Promises
            var velocityPromise = metricsDataService.getVelocityData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);

            // Predictability Graph Promises
            var predictabilityPromise = metricsDataService.getPredictabilityData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);

            // LeadTime Graph Promises
            var workStatesPromise = metricsDataService.getWorkStates(vm.selectedWorkTypes,vm.selectedProject.id, vm.searchDays, dateSince, dateUntil);
            var leadTimePromise = metricsDataService.getLeadTimeData(vm.selectedWorkTypes,vm.selectedProject.id,vm.searchDays, dateSince, dateUntil);


            // ================== START throughputGitRepoPromise ================
            throughputGitRepoPromise.then(function(response) {
                // console.log('throughputGitRepoPromise returned ', response.status, ' with response data: ', response.data);
                for (var repo in response.data) {
                    var repoName = response.data[repo];
                    gitData[repoName] = {};
                }
                if (response.data.length > 0) {
                    vm.hasGitRepo = true;
                }
                // ================== START throughputGitTagPromise ==================
                throughputGitTagPromise.then(function(response) {
                    // console.log('throughputGitTagPromise returned ', response.status, ' with response data: ', response.data);
                    for (var repo in response.data) {
                        var tags = response.data[repo];
                        for (var tag in tags) {
                            var date = response.data[repo][tag][0];
                            var tagName = response.data[repo][tag][1];
                            gitData[repo][date] = tagName;
                        }
                        if (tags.length > 0) {
                            vm.hasGitTag = true;
                        }
                    }
                    // Build Throughput Graph
                    // ================== START throughputHistoryPromise ================
                    throughputHistoryPromise.then(function(response) {
                        // console.log('throughputHistoryPromise returned ', response.status, ' with response data: ', response.data);
                        
                        //split response.data because it contains throughput data and tickets
                        var ticketStrings = response.data.slice(response.data.indexOf("tickets"))
                        //zeroeth index is "tickets", not needed anymore
                        ticketStrings = ticketStrings.splice(1);
                        //add parenbtheses to each string for easier copy and paste into JIRA
                        for(var i=0; i<ticketStrings.length; i++){
                            throughputTickets[i]="(" + ticketStrings[i][1] + ")";
                        };

                        var dataPoints = [];
                        straightDataPoints = [];
                        for (var tuple in response.data) {
                            var indexString = response.data[tuple][0];
                            if(indexString.includes("Straight")){
                                if(indexString == "ninetiethStraight" || indexString == "eightiethStraight")
                                    continue;
                                else{
                                    if (indexString == 'tenthStraight') {
                                        indexString = '90%';
                                    } else if (indexString == 'twentiethStraight') {
                                        indexString = '80%';
                                    } else if (indexString == 'fiftiethStraight') {
                                        indexString = '50%';
                                    }
                                    straightDataPoints[indexString] = response.data[tuple][1];
                                }
                            }
                            else
                                dataPoints.push(response.data[tuple][1]);
                        }

                        throughputData['Actual'] = dataPoints;

                        // ================== START throughputStatisticsPromise ============
                        throughputStatisticsPromise.then(function(response) {
                            //console.log('throughputStatisticsPromise returned ', response.status, ' with response data: ', response.data);
                            for (var key in response.data) {
                                var insertKey = '';
                                if (key == 'ninetieth') {
                                    continue;
                                } else if (key == 'eightieth') {
                                    continue;
                                } else if (key == 'fiftieth') {
                                    insertKey = '50%';
                                } else if (key == 'twentieth') {
                                    insertKey = '80%';
                                } else if (key == 'tenth') {
                                    insertKey = '90%';
                                }

                                var weeks = response.data[key];
                                var dataPoints = [];
                                for (var week in weeks) {
                                    dataPoints.push(weeks[week][1]);
                                }
                                curvedDataPoints[insertKey] = dataPoints;
                            }
                            var weeks = response.data[Object.keys(response.data)[0]];
                            for (var week in weeks) {
                                throughputLabels.push(weeks[week][0]);
                            }

                            for (var key in curvedDataPoints) {
                                throughputData[key] = curvedDataPoints[key];
                            }
                            googleChartApiPromise.then(buildThroughputGraph) // <---
                        }).catch(function(errorResponse) {
                            // console.log('throughputStatisticsPromise failed: ', errorResponse);
                            errorHandler(errorResponse, 'throughput');
                        });
                        // ================== END throughputStatisticsPromise ===============

                    }).catch(function(errorResponse) {
                        // console.log('throughputHistoryPromise failed: ', errorResponse);
                        errorHandler(errorResponse, 'throughput');
                    });
                    // ================== END throughputHistoryPromise ==================

                    // Build Velocity Graph
                    // ================== START velocityPromise =================================
                    velocityPromise.then(function(response) {
                        // console.log('velocityPromise returned ', response.status, ' with response data: ', response.data);
                        var backlogSize = 0;
                        absoluteBacklogHistory = [], relativeBacklogHistory = [], backlogSeries = [];

                        for (var key in response.data) {
                            var weeks = response.data[key];
                            var dataPoints = [];
                            for (var week in weeks) {
                                if (week == 0) {
                                    backlogSize = weeks[week][1];
                                    continue;
                                }
                                dataPoints.push(weeks[week][1]);
                            }
                            var tmpRelativeBacklogHistory = [];
                            for (var i = 0; i <= dataPoints.length-1; i++) {
                                tmpRelativeBacklogHistory.push(dataPoints[i] - backlogSize);
                            }
                            backlogSeries.push(key);
                            absoluteBacklogHistory.push(dataPoints);
                            relativeBacklogHistory.push(tmpRelativeBacklogHistory);
                        }
                        var weeks = response.data[Object.keys(response.data)[0]];
                        for (var week in weeks) {
                            velocityLabels.push(weeks[week][0]);
                        }
                        velocityLabels = velocityLabels.slice(1,velocityLabels.length);
                        velocityData = absoluteBacklogHistory;
                        vm.velocityRelative = false;
                        googleChartApiPromise.then(buildVelocityGraph); // <---
                    }).catch(function(errorResponse) {
                        // console.log('velocityPromise failed: ', errorResponse);
                        errorHandler(errorResponse, 'velocity');
                    });
                    // ================== END velocityPromise ===================================

                    // Build Predictability Graph
                    // ================== START predictabilityPromise  ==========================
                    predictabilityPromise.then(function(response) {
                        // console.log('predictabilityPromise returned ', response.status, ' with response data: ', response.data);
                        var dataPoints = [];
                        for (var week in response.data) {
                            predictabilityLabels.push(response.data[week][0]);
                            dataPoints.push(response.data[week][1]);
                        }
                        predictabilityData = dataPoints;
                        googleChartApiPromise.then(buildPredictabilityGraph); // <---
                    }).catch(function(errorResponse) {
                        // console.log('predictabilityPromise failed: ', errorResponse);
                        errorHandler(errorResponse, 'predictability');
                    });
                    // ================== END predictabilityPromise  ==========================

                    // Build Lead Time Graph
                    // ================== START workStatesPromise  ==========================
                    workStatesPromise.then(function(response) {
                        // console.log('workStatesPromise returned ', response.status, ' with response data: ', response.data);
                        var workStates= {'Overall': 0};
                        for (var i in response.data['workStates']){
                            workStates[response.data['workStates'][i]['name']] = i + 1;
                        }
                        // ================== START leadTimePromise ==========================
                        leadTimePromise.then(function(response) {
                            // console.log('leadTimePromise returned ', response.status, ' with response data: ', response.data);
                            leadTimeStages = new Array(Object.keys(workStates).length).fill(null);
                            leadTimeStages = leadTimeStages.filter(function(n){ return n != undefined });
                            for (var key in response.data) {
                                var stages = response.data[key];
                                var insertKey = '';
                                if (key == 'ninetieth'){
                                    insertKey = '90%';
                                } else if (key == 'eightieth') {
                                    insertKey = '80%';
                                } else if (key == 'fiftieth') {
                                    insertKey = '50%';
                                }
                                leadTimeData[insertKey] = new Array(Object.keys(workStates).length).fill(0);
                                for (var stage in stages) {
                                    var tmpLabels = [];
                                    var dataPoints = [];
                                    var weeks = stages[stage];
                                    for (var week in weeks){
                                        tmpLabels.push(weeks[week][0]);
                                        dataPoints.push(weeks[week][1]);
                                    }
                                    leadTimeData[insertKey][parseInt(workStates[stage])] = dataPoints;
                                    leadTimeStages[parseInt(workStates[stage])] = stage;
                                    if (leadTimeLabels.length < 1){
                                        leadTimeLabels = (tmpLabels);
                                    }
                                }
                            }
                            vm.leadTimeTrends = false;
                            vm.leadTimeMode = 'overall';
                            vm.leadTimePercentile = '90%';
                            googleChartApiPromise.then(buildOverallLeadTimeGraph); // <---

                        }).catch(function(errorResponse) {
                            // console.log('leadTimePromise failed: ', errorResponse);
                            errorHandler(errorResponse, 'leadTime');
                        });
                        // ================== END leadTimePromise ==========================
                    }).catch(function(errorResponse) {
                        // console.log('workStatesPromise failed: ', errorResponse);
                        errorHandler(errorResponse, 'leadTime');
                    });
                    // ================== END workStatesPromise ==========================

                }).catch(function(errorResponse) {
                    // console.log('throughputGitTagPromise failed: ', errorResponse);
                    vm.hasGitTag = false;
                    errorHandler(errorResponse, 'gitTag');
                });
                // ================== END throughputGitTagPromise ====================

            }).catch(function(errorResponse) {
                // console.log('throughputGitRepoPromise failed: ', errorResponse);
                vm.hasGitRepo = false;
                errorHandler(errorResponse, 'gitRepo');
            });
            // ================== END throughputGitRepoPromise ==================
            
            //build new URL for reports
            changeSelectedWorkTypes();
        }
    }
})();
