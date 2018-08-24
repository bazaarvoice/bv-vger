/*
 *  Controller for the editWorkStates.html, editWorkTypes.html and editProject.html
 */

(function(){
    'use strict';

    angular.module('vgerConfigurationsController', [])
    .controller('configurationsController', configurationsController)
    .filter('trusted', trusted)
    .config(function($mdThemingProvider, $mdIconProvider) {
        $mdThemingProvider
        .theme('default')
        .primaryPalette('blue-grey')
        .accentPalette('blue-grey')
        .warnPalette('deep-orange')
        .backgroundPalette('grey');
    
        $mdThemingProvider.theme('selected-card').backgroundPalette('teal', {
          'default': '400',
          'hue-1': '100',
          'hue-2': '600',
          'hue-3': 'A100'
      });
        
        $mdThemingProvider.theme('unselected-card').backgroundPalette('blue-grey', {
          'default': '400',
          'hue-1': '100',
          'hue-2': '600',
          'hue-3': 'A100'
      });
      
      $mdIconProvider.fontSet('md', 'material-icons');
    });
    
    // Allows custom styling on ngSanitize
    trusted.$inject = ['$sce'];
    function trusted($sce) {
        return function(html){
            return $sce.trustAsHtml(html)
        }
    }
    
    configurationsController.$inject = ['$scope', '$rootScope', '$window', '$location', '$mdToast', '$sanitize', 'configurationsService'];
    function configurationsController($scope, $rootScope, $window, $location, $mdToast, $sanitize, configurationsService) {
        var vm = this; // view-model
        var promiseTeam = configurationsService.getTeams();
        
        // UI elements
        vm.teams = [];
        vm.projects = [];
        vm.selectedTeam = {};
        vm.selectedProject = {};
        vm.getConfiguration = getConfiguration;
        vm.onDrop = onDrop;
        vm.onDropStates = onDropStates;
        vm.createNewState = createNewState;
        vm.createNewType = createNewType;
        vm.cancelNewState = cancelNewState;
        vm.cancelNewType = cancelNewType;
        vm.saveNewState = saveNewState;
        vm.saveNewType = saveNewType;
        vm.deleteState = deleteState;
        vm.deleteType = deleteType;
        vm.projectETL = projectETL;
        vm.issueTypeETL = issueTypeETL;
        vm.disableETL = false;
        vm.creatingNewState = false;
        vm.creatingNewType = false;
        
        vm.selectLeadTime = selectLeadTime;
        vm.startLeadTime;
        vm.endLeadTime;
        vm.selectedStartLeadTime = false;
        vm.selectedEndLeadTime = false;
        vm.newStateError = false;
        vm.newTypeError = false;
        vm.currentStart;
        vm.currentEnd;

        // Configuration data variable
        vm.jiraConfigData;
        vm.jiraIssueConfigData;
        vm.jiraWorkTypes = [];
        vm.jiraWorkStates = [];
        vm.issueFilter;
        vm.includeSubtasks = false;
        vm.excludedIssueTypes = [];
        vm.repos = [];
        vm.errorMessage;
        vm.showDeleteButton = false;
        
        vm.updateProjectSettings = updateProjectSettings;
        vm.updateWorkTypes = updateWorkTypes;
        vm.updateWorkStates = updateWorkStates;
        vm.getIssueFilter = getIssueFilter;
        vm.resetToBoard = resetToBoard;
        vm.resetJQLToBoard = resetJQLToBoard;

        
        var issueSuccess = false;
        vm.loading = false;
        getSessionScope();
        getConfiguration();

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
                vm.selectedTeam.id = $window.sessionStorage.selectedTeamId;
                vm.selectedProject.id = $window.sessionStorage.selectedProjectId;
                vm.selectedTeam.name = $window.sessionStorage.selectedTeamName;
                vm.selectedProject.name = $window.sessionStorage.selectedProjectName;
            }
        }


        // When Team and Project has been selected, fetch their configurations
        function getConfiguration() {
            getJiraIssueConfiguration();
            getJiraWorkTypesConfiguration();
            getJiraWorkStatesConfiguration();
            getGitConfiguration();
            getETLStatus();
        }

        function getIssueFilter(jql) {
            var promiseIssueFilter = configurationsService.getIssueFilter(jql);
            promiseIssueFilter.then(function(response) {
                var issueFilterData = response['data'];
                var dateFieldIndex = issueFilterData['dateFieldIndex'];
                var issueTypeFieldIndex = issueFilterData['issueTypeFieldIndex'];
                vm.issueFilter = issueFilterData['filteredJQL'];

                var warningIndex = [];
                for (var i in dateFieldIndex) {
                    warningIndex.push([dateFieldIndex[i], 'date']);
                }
                for (var i in issueTypeFieldIndex) {
                    warningIndex.push([issueTypeFieldIndex[i], 'issueType']);
                }
                if (dateFieldIndex.length > 0 || issueTypeFieldIndex.length > 0) {
                    vm.showWarning = true;
                } else {
                    vm.showWarning = false;
                }

                // order by smallest to greatest starting index
                warningIndex.sort(function(a,b){return a[0][0] > b[0][0]});

                // define custom insert string function
                String.prototype.insert = function (index, string) {
                    if (index > 0) {
                        return this.substring(0, index) + string + this.substring(index, this.length);
                    } else {
                        return string + this;
                    }
                };

                // highlights the query that should be removed (rendered as HTML using ngSanitize)
                var openSpanDateField = '<span style="background-color: #ffc9c9">';
                var openSpanIssueTypeField = '<span style="background-color: #F7DC6F">'
                var closeSpan = '</span>';
                var index = 0;
                vm.issueFilterHTML = vm.issueFilter;
                
                // finding beginning and ending of the string indices
                for (var i in warningIndex) {
                    if (warningIndex[i][1] == 'date') {
                        vm.issueFilterHTML = vm.issueFilterHTML.insert(index + warningIndex[i][0][0], openSpanDateField);
                        index += openSpanDateField.length;
                    }
                    else if (warningIndex[i][1] == 'issueType'){
                        vm.issueFilterHTML = vm.issueFilterHTML.insert(index + warningIndex[i][0][0], openSpanIssueTypeField);
                        index += openSpanIssueTypeField.length;
                    }
                    vm.issueFilterHTML = vm.issueFilterHTML.insert(index + warningIndex[i][0][1], closeSpan);
                    index += closeSpan.length;
                }
                
            }).catch(function(errorResponse) {
                console.log('promiseIssueFilter failed');
                vm.errorMessage = errorResponse;
            });
        }

        // Fetch jira issue configuration
        function getJiraIssueConfiguration() {
            var promiseJiraIssueConfiguration = configurationsService.getJiraIssueConfiguration(vm.selectedProject.id);
            promiseJiraIssueConfiguration.then(function(response) {
                vm.jiraIssueConfigData = response['data'];
                vm.boardName = vm.jiraIssueConfigData['boardName'];
                vm.projectName = vm.jiraIssueConfigData['name'];
                vm.includeSubtasks = vm.jiraIssueConfigData['includeSubtasks'];
                if (vm.jiraIssueConfigData['excludedIssueTypes'] != "") {
                    vm.excludedIssueTypes = vm.jiraIssueConfigData['excludedIssueTypes'].split(',');
                } 
                else {
                    vm.excludedIssueTypes = [];
                }
                vm.getIssueFilter(vm.jiraIssueConfigData['issueFilter']);
                
            }).catch(function(errorResponse) {
                console.log('promiseJiraIssueConfiguration failed');
                vm.errorMessage = errorResponse;
            });
        }

        // Fetch list of jira issue types & work types 
        function getJiraWorkTypesConfiguration() {
            var promiseJiraWorkTypesConfiguration = configurationsService.getJiraWorkTypesConfiguration(vm.selectedProject.id);
            promiseJiraWorkTypesConfiguration.then(function(response) {
                vm.jiraWorkTypes = response['data'];
                var temp = [];
                for (var i in vm.jiraWorkTypes) {
                    var workType = {};
                    workType['workTypeName'] = i;
                    workType['issueTypes'] = [];
                    for (var j in vm.jiraWorkTypes[i]) {
                        var issueType = {};
                        issueType['label'] = vm.jiraWorkTypes[i][j];
                        issueType['selected'] = false;
                        workType['issueTypes'].push(issueType);
                    }
                    temp.push(workType)
                }
                // Sort alphanumerically
                temp = sortByKey(temp, 'workTypeName');
                vm.jiraWorkTypes = temp;
            }).catch(function(errorResponse) {
                console.log('promiseJiraWorkTypesConfiguration failed');
                vm.errorMessage = errorResponse;
            });
        }
        
        // Fetch list of all jira ticket status and its work states
        function getJiraWorkStatesConfiguration() {
            var promiseJiraWorkStatesConfiguration = configurationsService.getJiraWorkStatesConfiguration(vm.selectedProject.id);
            promiseJiraWorkStatesConfiguration.then(function(response) {
                vm.defaultLeadTimeEndState = response['data']['defaultLeadTimeEndState']; 
                vm.defaultLeadTimeStartState = response['data']['defaultLeadTimeStartState'];
                vm.jiraWorkStates = response['data']['workStates'];
                // Find the index of default start/end lead time
                for (var i in vm.jiraWorkStates) {
                    if (vm.jiraWorkStates[i]['name'] == vm.defaultLeadTimeStartState) {
                        var start = Number(i);
                        vm.currentStart = start;
                    } else if (vm.jiraWorkStates[i]['name'] == vm.defaultLeadTimeEndState) {
                        var end = Number(i) - 1;
                        vm.currentEnd = end;
                    }
                    
                    // Give temporary index
                    vm.jiraWorkStates[i]['index'] = Number(i);

                    // Find status that belongs to the state
                    for (var status in vm.jiraWorkStates[i]['status']) {
                        var label = vm.jiraWorkStates[i]['status'][status];
                        vm.jiraWorkStates[i]['status'][status] = {
                            'label': label,
                            'selected': false,
                        }
                    }
                }
                
                for (var i in vm.jiraWorkStates) {
                    if (i >= start && i <=end) {
                        vm.jiraWorkStates[i]['selected'] = true;
                    } else {
                        vm.jiraWorkStates[i]['selected'] = false;
                    }
                }
            }).catch(function(errorResponse) {
                vm.errorMessage = errorResponse;
            });
        }

        // Fetch list of git repositories
        function getGitConfiguration() {
            var promiseProjectRepos = configurationsService.getGitConfiguration(vm.selectedProject.id);
            promiseProjectRepos.then(function(response) {
                vm.repos = response['data'];
            }).catch(function(errorResponse) {
                console.log('getGitConfiguration failed');
                vm.errorMessage = errorResponse;
            });
        }

        // -------------------------------------
        // Functions for UI element interactions
        // -------------------------------------
        // Drag and drop helper function
        function onDrop (srcList, srcIndex, targetList, targetIndex) {
            // Copy the item from source to target.
            targetList.splice(targetIndex, 0, srcList[srcIndex]);
            // Remove the item from the source, possibly correcting the index first.
            // We must do this immediately, otherwise ng-repeat complains about duplicates.
            if (srcList == targetList && targetIndex <= srcIndex) srcIndex++;
            srcList.splice(srcIndex, 1);
            // By returning true from dnd-drop we signalize we already inserted the item.
            return true;
        };
        
        function onDropStates (srcList, srcIndex, targetList, targetIndex) {
            // Copy the item from source to target.
            targetList.splice(targetIndex, 0, srcList[srcIndex]);
            // Remove the item from the source, possibly correcting the index first.
            // We must do this immediately, otherwise ng-repeat complains about duplicates.
            if (srcList == targetList && targetIndex <= srcIndex) srcIndex++;
            srcList.splice(srcIndex, 1);
            // By returning true from dnd-drop we signalize we already inserted the item.

            // Fix ordering
            // vm.jiraWorkStates[targetIndex].index = targetIndex;
            
            if(srcIndex > targetIndex) {
                for (var i=targetIndex; i< srcIndex; i++) {
                    vm.jiraWorkStates[i].index = i;
                }
            } else {
                for (var i=srcIndex; i< targetIndex; i++) {
                    vm.jiraWorkStates[i].index = i;
                }
            }
            // Fix currentStart and currentEnd
            for (var j=0; j<vm.jiraWorkStates.length; j++) {
                if (vm.jiraWorkStates[j].selected) {
                    if (j < vm.currentStart) {
                        vm.currentStart = j;
                    } else if (j > vm.currentEnd) {
                        vm.currentEnd = j;
                    }
                }
            }
            for (var j=vm.currentStart; j<=vm.currentEnd; j++) {
                vm.jiraWorkStates[j].selected = true;
            }

            return true;
        };

        function sortByKey(array, key) {
            return array.sort(function(a, b) {
                var x = a[key];
                var y = b[key];
                // Format to lower case
                if (typeof x == "string") {
                    x = x.toLowerCase();
                }
                if (typeof y == "string") {
                    y = y.toLowerCase();
                }
                // Compare string
                if (x < y) {
                    return -1;
                } else if (x > y) {
                    return 1;
                } else {
                    return 0;
                }
            });
        }
        
        function selectLeadTime(state) {
            if (vm.currentEnd == vm.currentStart) {
                state.selected = true;
            }
             
            if (state.selected) {
                // Reevaluate start/end leadtime when card is selected into to leadtime 
                if (state.index < vm.currentStart) {
                    vm.currentStart =  state.index;
                } else if (state.index > vm.currentEnd) {
                    vm.currentEnd = state.index;
                }
                
                // fill up gaps
                if (vm.currentStart < vm.currentEnd) {
                    for (var i=vm.currentStart; i<=vm.currentEnd; i++) {
                        vm.jiraWorkStates[i].selected = true;
                    }
                } else if (vm.currentStart > vm.currentEnd) {
                    for (var i=vm.currentEnd; i<=vm.currentStart; i++) {
                        vm.jiraWorkStates[i].selected = true;
                    }
                }
            } else {
                // Reevaluate start/end leadtime when card is unselected from leadtime
                if (state.index == vm.currentStart) {
                    vm.currentStart += 1;
                } else if (state.index == vm.currentEnd) {
                    vm.currentEnd -= 1;
                }
            }

        }
        
        function warningToast(message) {
            var el = angular.element(document.querySelector('#toastContainer'));
            $mdToast.show(
                $mdToast.simple()
                    .textContent(message)
                    .parent(el)
                    .action('OK')
                    .highlightAction(true)
                    .highlightClass('md-accent')
                    .position('top right')
                    .hideDelay(5000)
            );
        }
        
        function createNewState() {
            vm.creatingNewState = true;
        }
        
        function createNewType() {
            vm.creatingNewType = true;
        }
        
        function cancelNewState() {
            vm.creatingNewState = false;
        }
        
        function cancelNewType() {
            vm.creatingNewType = false;
        }
        
        function saveNewState() {
            vm.newStateError = false;
            
            // Check that state name doesn't already exists
            for (var i in vm.jiraWorkStates) {
                if (vm.jiraWorkStates[i]['name'].toLowerCase() == vm.newStateName.toLowerCase()) {
                    warningToast('State name already exists');
                    vm.newStateError = true;
                }
            }
            
            if (!vm.newStateError) {
                vm.creatingNewState = false;
                
                // move all other elements 
                for (var i in vm.jiraWorkStates) {
                    vm.jiraWorkStates[i]['index'] += 1;
                }
                
                // create new state
                var newState = {
                    'status': [],
                    'name': vm.newStateName,
                    'index': 0,
                    'selected': false
                }
                vm.jiraWorkStates.unshift(newState); // push new state at the start of array
                vm.currentEnd += 1;
                vm.currentStart += 1;
                
                // clear newStateName
                vm.newStateName = '';
            }
        }

        function saveNewType() {
            vm.newTypeError = false;
            
            // Check that type name doesn't already exists
            for (var i in vm.jiraWorkTypes) {
                if (vm.jiraWorkTypes[i]['workTypeName'].toLowerCase() == vm.newTypeName.toLowerCase()) {
                    warningToast('Type name already exists');
                    vm.newTypeError = true;
                }
            }

            if (!vm.newTypeError) {
                vm.creatingNewType = false;
                // create new type
                var newType = {
                    'workTypeName': vm.newTypeName,
                    'issueTypes': []
                }
                vm.jiraWorkTypes.unshift(newType); // push new state at the start of array

                // clear newStateName
                vm.newTypeName = '';
                sortByKey(vm.jiraWorkTypes, 'workTypeName');
            }
        }
        
        function deleteState($event, state) {
            if (state.index >= vm.currentStart && state.index <= vm.currentEnd) {
                vm.currentEnd--;
            }

            $event.stopPropagation(); // prevents clicking delete button from propagating to card selection event
            for (var i=0; i < vm.jiraWorkStates.length; i++) {
                var obj = vm.jiraWorkStates[i];
                if (state.name == obj['name']) {
                    vm.jiraWorkStates.splice(i, 1);
                    i--;
                }
            }
            // iterate through jiraworkstate again and reevaluate order
            for (var i=0; i<vm.jiraWorkStates.length; i++) {
                vm.jiraWorkStates[i].index = i;
            }
            
        }
        
        function deleteType(type) {
            for (var i=0; i < vm.jiraWorkTypes.length; i++) {
                var obj = vm.jiraWorkTypes[i];
                if (type.workTypeName == obj['workTypeName']) {
                    vm.jiraWorkTypes.splice(i, 1);
                    i--;
                }
            }
        }
        
        function updateProjectSettings() {
            vm.loading = true;
            updateIssues();
        }
        
        function updateIssues() {
            // TODO: validate chip input format --> From Projects: GOPS  all caps
            //                                  --> Except For: Epic     first letter uppercase
            // value validation is done on backend/lambda
            
            if(vm.selectedProject) {
                var promiseUpdateIssues = configurationsService.updateIssues(
                    vm.selectedProject.id,
                    vm.boardName,
                    vm.includeSubtasks,
                    vm.excludedIssueTypes.join(','),
                    vm.issueFilter,
                    vm.selectedProject.name
                );
                promiseUpdateIssues.then(function(response) {
                    if (response['status'] == '200') {
                        // warningToast('Saved!');
                        updateRepos();
                    }
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    warningToast(errorResponse['data']['message']);
                }).then(function(){
                    vm.loading = false;
                });
            }
        }
        
        function updateRepos() {
            if(vm.selectedProject) {
                var promiseUpdateRepos = configurationsService.updateRepos(vm.selectedProject.id, vm.repos);
                promiseUpdateRepos.then(function(response) {
                    warningToast('Saved');
                    setTimeout(function() {
                        $rootScope.selectedProjectId = vm.selectedProject.id;
                        $rootScope.selectedProjectName = vm.selectedProject.name;
                        $window.sessionStorage.selectedProjectId = vm.selectedProject.id;
                        $window.sessionStorage.selectedProjectName = vm.selectedProject.name;
                        window.location.href = "#!/metrics";
                        window.location.reload()
                    }, 2000)
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    warningToast(errorResponse['data']['message']);
                });
            }
        }
        
        function updateWorkTypes() {
            vm.loading = true;
            if(vm.selectedProject) {
                // Build POST data body
                var workTypePostBody = {};
                for (var i in vm.jiraWorkTypes) {
                    var issueList = [];
                    for (var j in vm.jiraWorkTypes[i].issueTypes) {
                        issueList.push(vm.jiraWorkTypes[i].issueTypes[j].label);
                    }
                    workTypePostBody[vm.jiraWorkTypes[i].workTypeName] = issueList;
                }
                var promiseUpdateWorkTypes = configurationsService.updateWorkTypes(vm.selectedProject.id, workTypePostBody);
                promiseUpdateWorkTypes.then(function(response) {
                    if (response['status'] == '200') {
                        warningToast('Saved!');
                    }
                    
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    warningToast(errorResponse['data']['message']);
                }).then(function() {
                    vm.loading = false;
                });
            }
        }
        
        function resetToBoard() {
            vm.loading = true;
            var promiseBoardWorkStatesConfiguration = configurationsService.getBoardWorkStatesConfiguration(vm.selectedProject.id);
            promiseBoardWorkStatesConfiguration.then(function(response) {
                if (response['status'] == '200') {
                    vm.defaultLeadTimeEndState = response['data']['defaultLeadTimeEndState']; 
                    vm.defaultLeadTimeStartState = response['data']['defaultLeadTimeStartState'];
                    vm.jiraWorkStates = response['data']['workStates'];
                    // Find the index of default start/end lead time
                    for (var i in vm.jiraWorkStates) {
                        if (vm.jiraWorkStates[i]['name'] == vm.defaultLeadTimeStartState) {
                            var start = Number(i);
                            vm.currentStart = start;
                        } else if (vm.jiraWorkStates[i]['name'] == vm.defaultLeadTimeEndState) {
                            var end = Number(i) - 1;
                            vm.currentEnd = end;
                        }
                    
                        // Give temporary index
                        vm.jiraWorkStates[i]['index'] = Number(i);
                    
                        // Find status that belongs to the state
                        for (var status in vm.jiraWorkStates[i]['status']) {
                            var label = vm.jiraWorkStates[i]['status'][status];
                            vm.jiraWorkStates[i]['status'][status] = {
                                'label': label,
                                'selected': false,
                            }
                        }
                    }
                    
                    for (var i in vm.jiraWorkStates) {
                        if (i >= start && i <=end) {
                            vm.jiraWorkStates[i]['selected'] = true;
                        } else {
                            vm.jiraWorkStates[i]['selected'] = false;
                        }
                    }
                    warningToast('Reverted to board configuration! Click the save button to keep all changes.');
                }
            }).catch(function(errorResponse){
                console.log(errorResponse);
                warningToast(errorResponse['data']['message']);
            }).then(function() {
                vm.loading = false;
            });
        }
        
        function updateWorkStates() {
            vm.loading = true;
            if(vm.selectedProject) {
                // Build POST data body
                var workStates = [];
                var defaultLeadTimeStart = vm.jiraWorkStates.length;
                var defaultLeadTimeEnd = 0;
                for (var i in vm.jiraWorkStates) {
                    if (vm.jiraWorkStates[i].selected) {

                        if (defaultLeadTimeStart > vm.jiraWorkStates[i].index) {
                            defaultLeadTimeStart = vm.jiraWorkStates[i].index;
                            vm.defaultLeadTimeStartState = vm.jiraWorkStates[i].name;
                        }
                        if (defaultLeadTimeEnd < vm.jiraWorkStates[i].index + 1) {
                            defaultLeadTimeEnd = vm.jiraWorkStates[i].index + 1;
                            vm.defaultLeadTimeEndState = vm.jiraWorkStates[parseInt(i)+1].name;
                        }
                    }
                    var statusList = [];
                    for (var j in vm.jiraWorkStates[i].status) {
                        statusList.push(vm.jiraWorkStates[i].status[j].label);
                    }
                    workStates.push({
                        'status': statusList,
                        'name': vm.jiraWorkStates[i].name
                    });
                }

                var workStatePostBody = {
                    'defaultLeadTimeStartState': vm.defaultLeadTimeStartState,
                    'defaultLeadTimeEndState': vm.defaultLeadTimeEndState,
                    'workStates': workStates
                }; 
                var promiseUpdateWorkStates = configurationsService.updateWorkStates(vm.selectedProject.id, workStatePostBody);
                promiseUpdateWorkStates.then(function(response) {
                    if (response['status'] == '200') {
                        warningToast('Saved!');
                    }
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    warningToast(errorResponse['data']['message']);
                }).then(function() {
                    vm.loading = false;
                });
            }
        }

        function resetJQLToBoard() {
            if (vm.boardName) {
                var JQLPromise = configurationsService.getBoardJQL(vm.boardName);
                JQLPromise.then(function(response) {
                    vm.issueFilter = response['data']['issue_filter'];
                    getIssueFilter(vm.issueFilter);
                }).catch(function(errorResponse) {
                    console.log(errorResponse);
                    warningToast(errorResponse['data']['message']);
                })
            } else {
                warningToast("Missing board name!")
            }
        }

        function projectETL() {
            var projectETLPromise = configurationsService.projectETL(vm.selectedProject.id, false);
            projectETLPromise.then(function(response) {
                warningToast("Successfully triggered ETL for " + vm.selectedProject.name + ". Please come back later when data gets loaded.");
                vm.disableETL = true;
            }).catch(function(errorResponse) {
                warningToast(errorResponse.data)
            })
        }

        function issueTypeETL() {
            var issueTypeETLPromise = configurationsService.projectETL(vm.selectedProject.id, true);
            issueTypeETLPromise.then(function(response) {
                warningToast("Successfully triggered issue type ETL.");
                setTimeout(function() {
                    window.location.reload()
                }, 2500)
            }).catch(function(errorResponse) {
                warningToast(errorResponse.data)
            })
        }

        function getETLStatus() {
            var etlStatusPromise = configurationsService.etlStatus(vm.selectedProject.id);
            etlStatusPromise.then(function(response) {
                var last_etl_run = response["data"]["last_etl_run"];
                var current_time = new Date().getTime() / 1000;
                if (last_etl_run != null && (current_time - last_etl_run) < 300) {
                    vm.disableETL = true;
                }
            })
        }
    }

})();