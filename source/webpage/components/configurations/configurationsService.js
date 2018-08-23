/*
 * Service to handle API requests made from configurationsController
 * Create, update, retrieve configuration info from db
 */

(function(){
    'use strict';

    angular.module('vgerConfigurationsService', [])
    .service('configurationsService', configurationsService);

    configurationsService.$inject = ['$http', 'routerConfig'];
    function configurationsService($http, routerConfig) {
        var service = {
            getTeams: getTeams,
            getProjects: getProjects,
            getJiraIssueConfiguration: getJiraIssueConfiguration,
            getJiraWorkTypesConfiguration: getJiraWorkTypesConfiguration,
            getJiraWorkStatesConfiguration: getJiraWorkStatesConfiguration,
            getBoardWorkStatesConfiguration: getBoardWorkStatesConfiguration,
            getGitConfiguration: getGitConfiguration,
            getIssueFilter: getIssueFilter,
            getBoardJQL: getBoardJQL,
            createTeam: createTeam,
            createProject: createProject,
            updateIssues: updateIssues,
            updateRepos: updateRepos,
            updateWorkTypes: updateWorkTypes,
            updateWorkStates: updateWorkStates,
            projectETL: projectETL,
            etlStatus: etlStatus
        };
        return service;

        // Return list of teams
        function getTeams() {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'team/')
            });
            return response;
        }
        
        // Return list of projects belongning to the team
        function getProjects(teamId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'team/' + teamId + '/' + 'project/')
            });
            return response;
        }
        
        // Return detailed jira issue information 
        function getJiraIssueConfiguration(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'issues')
            });
            return response;
        }

        // Return list of work types
        function getJiraWorkTypesConfiguration(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'worktypes')
            });
            return response;
        }
        
        // Return list of status and state names
        function getJiraWorkStatesConfiguration(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'workstates')
            });
            return response;
        }
        
        // Return list of status and state names from Kanaban board
        function getBoardWorkStatesConfiguration(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'boardworkstates')
            });
            return response;
        }
        
        // Return list of git repositories
        function getGitConfiguration(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'repos')
            });
            return response;
        }
        
        // Return filtered JQL and indices that requires warning
        function getIssueFilter(jql) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'issues/filter?jql=' + jql)
            });
            return response;
        }

        // Return latest JQL given JIRA board name
        function getBoardJQL(board_name) {
            var response = $http({
                method: "GET",
                url: encodeURI(routerConfig.apiGateway + 'board?boardName=' + board_name)
            });
            return response;
        }

        // Create a new team
        function createTeam(teamName) {
            var response = $http({
                method: 'POST',
                url: encodeURI(routerConfig.apiGateway + 'team/'),
                data: { 
                    name: teamName
                }
            });
            return response;
        }
        
        // Create a new project
        function createProject(teamId, projectName, boardName, issueKeys, repoNames) {
            var response = $http({
                method: 'POST',
                url: encodeURI(routerConfig.apiGateway + 'team/' + teamId + '/' + 'project'),
                data: { 
                    name: projectName,
                    issues: {
                        issueKeys: issueKeys,
                        boardName: boardName
                    },
                    repoNames: repoNames
                }
            });
            return response;
        }

        // Update project issues
        function updateIssues(projectId, boardName, includeSubtasks, excludedIssueTypes, issueFilter, projectName) {
            var response = $http({
                method: 'PUT',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'issues'),
                data: {
                    boardName: boardName,
                    includeSubtasks: includeSubtasks,
                    excludedIssueTypes: excludedIssueTypes,
                    issueFilter: issueFilter,
                    projectName: projectName
                }
            });
            return response;
        }
        
        function updateRepos(projectId, repos) {
            var response = $http({
                method: 'PUT',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'repos'),
                data: repos
            });
            return response;
        }
        
        // Update Work Types
        function updateWorkTypes(projectId, workTypePostBody) {
            var response = $http({
                method: 'PUT',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'worktypes'),
                data: workTypePostBody
            });
            return response;
        }
        
        // Update Work States
        function updateWorkStates(projectId, workStatePostBody) {
            var response = $http({
                method: 'PUT',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/' + 'workstates'),
                data: workStatePostBody
            });
            return response;
        }

        // Trigger ETL
        function projectETL(selectedProjectId, issue_type_etl) {
            var APIStr =
                routerConfig.apiGateway + 'project/' + selectedProjectId + '/etl';
            if (issue_type_etl) {
                APIStr += "?issuetype=true";
            }
            var response = $http({
                method: 'POST',
                url: encodeURI(APIStr)
            });
            return response;
        }

        // Get ETL status for specific project
        function etlStatus(selectedProjectId) {
            var APIStr =
                routerConfig.apiGateway + "project/" + selectedProjectId + "/etl/status";
            var response = $http({
                method: "GET",
                url: encodeURI(APIStr)
            });
            return response;
        }
    }

})();
