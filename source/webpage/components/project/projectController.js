(function(){
    'use strict';

    angular.module('vgerProject', [])
    .controller('projectController', projectController);
    
    projectController.$inject = ['$scope', '$location', '$rootScope', '$window', 'metricsFilterService', 'constantsService']
    function projectController($scope, $location, $rootScope, $window, metricsFilterService, constantsService) {
      
      var vm = this; // view-model

      vm.teams = [];
      vm.projects = [];
      vm.getProjectList = getProjectList;
      vm.getMetrics = getMetrics;
      vm.addWebpageConstants = addWebpageConstants;
      var selectedTeamId;
      var selectedTeamName;
      var selectedProjectId;
      var selectedProjectName;
      // getProjectList($rootScope.selectedTeamId, $rootScope.selectedTeamName);
      getProjectList($window.sessionStorage.selectedTeamId, $window.sessionStorage.selectedTeamName);
      addWebpageConstants();

      // Get list of projects for the selectedTeam
      function getProjectList(id, name) {
          var promiseProject = metricsFilterService.getProjects(id);
          promiseProject.then(function(response) {
              sortByKey(response.data, 'name');
              vm.projects = [];
              for (var key in response.data) {
                  vm.projects.push(response.data[key]);
              }
          }).catch(function(errorResponse) {
              console.log(errorResponse);
          });
      }

      function addWebpageConstants() {
        if(!$rootScope.VGER_GUIDE){
          constantsService.setRootScopeConstants();
        }
        var link = document.getElementById("vger_guide_link");
        link.href = $rootScope.VGER_GUIDE;

        link = document.getElementById("add_project_link");
        link.href = $rootScope.ADD_PROJECT_URL;        
      }
      
      function getMetrics(id, name) {
          selectedProjectId = id;
          selectedProjectName = name;
          $rootScope.selectedProjectId = selectedProjectId;
          $rootScope.selectedProjectName = selectedProjectName;
          $window.sessionStorage.selectedProjectId = selectedProjectId;
          $window.sessionStorage.selectedProjectName = selectedProjectName;
          
          $location.path('/metrics');
      }
      
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
      
    };
})();
