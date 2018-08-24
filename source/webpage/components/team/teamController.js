(function(){
    'use strict';

    angular.module('vgerTeam', [])
    .controller('teamController', teamController);
    
    teamController.$inject = ['$scope', '$location', '$rootScope', '$window', 'metricsFilterService', 'constantsService']
    function teamController($scope, $location, $rootScope, $window, metricsFilterService, constantsService) {
      
      var vm = this; // view-model
      
      vm.teams = [];
      vm.projects = [];
      vm.getProjectList = getProjectList;
      vm.getRootScope = getRootScope;
      vm.addWebpageConstants = addWebpageConstants;
      
      var selectedTeamId;
      var selectedTeamName;
      var selectedProjectId;
      var selectedProjectName;
      getTeamList();
      addWebpageConstants();
      
      function getRootScope() {
          getRootScopeTeam();
          getProjectList(vm.selectedTeam.id, vm.selectedTeam.name);
      };
      
      function getRootScopeTeam() {    
          if ($rootScope.selectedTeamId && $rootScope.selectedTeamName) {
              vm.selectedTeam = {};
              vm.selectedTeam.id = $rootScope.selectedTeamId;
              vm.selectedTeam.name = $rootScope.selectedTeamName;
          }
      };

      function addWebpageConstants() {
          if(!$rootScope.VGER_GUIDE){
            constantsService.setRootScopeConstants();
          }
          
          var link = document.getElementById("vger_guide_link")
          link.href = $rootScope.VGER_GUIDE;
          
          link = document.getElementById("add_team_link")
          link.href = $rootScope.ADD_PROJECT_URL;
      }
      
      // Get list of teams
      function getTeamList() {
          var promiseTeam = metricsFilterService.getTeams();
          promiseTeam.then(function(response) {
              sortByKey(response.data, 'name');
              for (var key in response.data) {
                  vm.teams.push(response.data[key]);
              }
          })
          // var promiseAvailableTeams = metricsFilterService.getAvailableTeams();
          //populate drop-down list with team names from rest api call
          // promiseAvailableTeams.then(function(response) {
            // var str = "";
            // var strArr, tempOpt;
            // for(var i=0; i<response.data.length; i++){
            //   strArr = response.data[i].name;
            //   strArr = strArr.split(" ");
            //   for(var j=0; j<strArr.length; j++){
            //     tempOpt = strArr[j].charAt(0).toUpperCase() + strArr[j].slice(1)
            //     str += tempOpt;
            //     if(j != strArr.length-1)
            //       str += " ";
            //   }
            //   options += "<option value='" + str + "'>"; 
            //   str = "";             
            // }       
            // var datalist = document.getElementById("teamNamesList");
            // datalist.innerHTML = options;
          // }).catch(function(errorResponse) {
          //     console.log(errorResponse);
          // });
      };
      
      // Get list of projects for the selectedTeam
      function getProjectList(id, name) {
          selectedTeamId = id;
          selectedTeamName = name;
          $rootScope.selectedTeamId = selectedTeamId;
          $rootScope.selectedTeamName = selectedTeamName;
          
          $window.sessionStorage.selectedTeamId = selectedTeamId;
          $window.sessionStorage.selectedTeamName = selectedTeamName;
          
          $rootScope.selectedProjectId = null;
          $rootScope.selectedProjectName = null;
          
          
          $location.path('/project');
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
    };
})();
