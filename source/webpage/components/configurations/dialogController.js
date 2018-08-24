/*
 *  Controller for the configurations page
 */

(function(){
    'use strict';

    angular.module('vgerDialogController', [])
    .controller('dialogController', dialogController);
    
    dialogController.$inject = ['$scope', '$rootScope', '$window', 'configurationsService', '$mdDialog', '$location'];
    function dialogController($scope, $rootScope, $window, configurationsService, $mdDialog, $location) {
        var vm = this; // view-model

        vm.addTeam = function(ev) {
            $mdDialog.show({
                controller: DialogController,
                templateUrl: 'addTeam.tmpl.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose:true,
                fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
            });
        };
        
        vm.addProject = function(ev) {
            $mdDialog.show({
                controller: ProjectDialogController,
                templateUrl: 'addProject.tmpl.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose:true,
                fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
            });
        };

        function DialogController($scope, $mdDialog) {

            $scope.hide = function() {
                $mdDialog.hide();
            };

            $scope.cancel = function() {
                $mdDialog.cancel();
            };

            $scope.checkInput = function() {    
                try{
                    var input = document.getElementById("teamName")
                    if($scope.teamName.length == null || $scope.teamName.length < 3) {
                        input.setAttribute('list', "");
                    }
                    else {
                        input.setAttribute('list', "teamNamesList");
                    }
                }
                catch(error){
                    //no need to do anything with error, handled with 'required'
                    //console.log(error)
                }
            };

            $scope.addTeam = function() {
                // Clear previous error/success/loading messages
                $scope.validationTeamErrorMessage = '';
                $scope.validationTeamSuccessMessage = '';
                $scope.loading = true;
                
                // Create team
                var promiseCreateTeam = configurationsService.createTeam($scope.teamName);
                promiseCreateTeam.then(function(response) {
                    // Parse the id of the team that has been created
                    console.log(response);
                    $scope.teamId = response['data']['id'];
                    
                    // Format csv to arrays
                    if ($scope.repoNames) {
                        $scope.repoNames = $scope.repoNames.split(',');
                    }
                    
                    // Create project
                    var promiseCreateProject = configurationsService.createProject($scope.teamId, $scope.projectName, $scope.boardName, $scope.repoNames);
                    promiseCreateProject.then(function(response) {
                        // $scope.validationTeamSuccessMessage = 'Successfully created team project!';
                        $mdDialog.hide();
                        
                        $rootScope.selectedProjectId = response['data']['id'];
                        $rootScope.selectedProjectName = response['data']['name'];
                        $window.sessionStorage.selectedProjectId = response['data']['id'];
                        $window.sessionStorage.selectedProjectName =  response['data']['name'];
                        
                        $location.path('/metrics').search({newTeamProject: 'true'});
                        
                    }).catch(function(errorResponse){
                        console.log(errorResponse);
                        $scope.validationTeamErrorMessage = errorResponse['data']['message'];
                    }).then(function() {
                        $scope.loading = false;
                    });
                    
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    $scope.validationTeamErrorMessage = errorResponse['data']['message'];
                    $scope.loading = false;
                });
            }
        }
        
        function ProjectDialogController($scope, $mdDialog) {
            $scope.teamId = $rootScope.selectedTeamId;
            $scope.teamName = $rootScope.selectedTeamName;
            
            $scope.hide = function() {
                $mdDialog.hide();
            };

            $scope.cancel = function() {
                $mdDialog.cancel();
            };

            $scope.addProject = function() {
                // Clear previous error/success/loading messages
                $scope.validationProjectErrorMessage = '';
                $scope.validationProjectSuccessMessage = '';
                $scope.loading = true;

                if ($scope.repoNames) {
                    $scope.repoNames = $scope.repoNames.split(',');
                }

                // Create project
                var promiseCreateProject = configurationsService.createProject($scope.teamId, $scope.projectName, $scope.boardName, $scope.repoNames);
                console.log($scope.projectName, $scope.boardName, $scope.repoNames);
                promiseCreateProject.then(function(response) {
                    console.log(response);
                    if (response['status'] == '201') {
                        // $scope.validationProjectSuccessMessage = 'Successfully created team project!';
                        $mdDialog.hide();
                        
                        $rootScope.selectedProjectId = response['data']['id'];
                        $rootScope.selectedProjectName = response['data']['name'];
                        $window.sessionStorage.selectedProjectId = response['data']['id'];
                        $window.sessionStorage.selectedProjectName =  response['data']['name'];
                        
                        $location.path('/metrics').search({newTeamProject: 'true'});

                    }
                }).catch(function(errorResponse){
                    console.log(errorResponse);
                    $scope.validationProjectErrorMessage = errorResponse['data']['message'];
                }).then(function() {
                    $scope.loading = false;
                });
            }
        }
    }

})();
