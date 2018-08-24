/*
 * Service to handle API requests made from metricsController
 */

(function(){
    'use strict';

    angular.module('vgerMetricsService', [])
    .service('metricsFilterService', metricsFilterService)
    .service('metricsDataService', metricsDataService);

    // Retrieves data for charts
    metricsDataService.$inject = ['$http', 'routerConfig', '$rootScope'];
    function metricsDataService($http, routerConfig, $rootScope) {
        var service = {
            getWorkStates: getWorkStates,
            getBoardID: getBoardID,
            getJiraIssueConfiguration: getJiraIssueConfiguration,
            getLeadTimeData: getLeadTimeData,
            getThroughputStatisticsData: getThroughputStatisticsData,
            getThroughputHistoryData: getThroughputHistoryData,
            getThroughputGitRepoData: getThroughputGitRepoData,
            getThroughputGitTagData: getThroughputGitTagData,
            getVelocityData: getVelocityData,
            getPredictabilityData: getPredictabilityData,
            getPRHistoryData: getPRHistoryData,
            getPRStatisticsData: getPRStatisticsData,
            getPRPredictabilityData: getPRPredictabilityData,
            getPRLeadtimeData: getPRLeadtimeData,
            getPRBacklogData: getPRBacklogData
        };
        
        return service;

        function getWorkStates(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var workStatesAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'workstates?';
            var response = $http({
                method: 'GET',
                url: encodeURI(workStatesAPIStr)
            });
            return response;
        }

        //  Get board ID to open JIRA board in new tab upon user request
        function getBoardID(boardName) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'board/id/?boardName=' + boardName)
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

        function getLeadTimeData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var leadTimeAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'leadtime?';

            if (workTypeStr != '') leadTimeAPIStr += '&workTypes=' + workTypeStr;
            if (days) leadTimeAPIStr += '&days=' + days;
            if (dateSince) leadTimeAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) leadTimeAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(leadTimeAPIStr)
            });
            return response;
        }

        function getThroughputStatisticsData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var statisticsStr = 'statistics';
            var statisticsAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'throughput/' + statisticsStr + '?';

            if (workTypeStr != '') statisticsAPIStr += '&workTypes=' + workTypeStr;
            if (days) statisticsAPIStr += '&days=' + days;
            if (dateSince) statisticsAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) statisticsAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(statisticsAPIStr)
            });
            return response;
        }

        function getThroughputHistoryData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var historyStr = 'history';
            var historyAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'throughput/' + historyStr + '?';

            if (workTypeStr != '') historyAPIStr += '&workTypes=' + workTypeStr;
            if (days) historyAPIStr += '&days=' + days;
            if (dateSince) historyAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) historyAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(historyAPIStr)
            });
            return response;
        }

        function getThroughputGitRepoData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var gitRepoAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'repos?';
            var response = $http({
                method: 'GET',
                url: encodeURI(gitRepoAPIStr)
            });
            return response;
        }

        function getThroughputGitTagData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var gitTagAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'tags?';

            if (days) gitTagAPIStr += '&days=' + days;
            if (dateSince) gitTagAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) gitTagAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(gitTagAPIStr)
            });
            return response;
        }

        function getVelocityData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var backlogHistoryAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'backlog/?';

            if (workTypeStr != '') backlogHistoryAPIStr += '&workTypes=' + workTypeStr;
            if (days) backlogHistoryAPIStr += '&days=' + days;
            if (dateSince) backlogHistoryAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) backlogHistoryAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(backlogHistoryAPIStr)
            });
            return response;
        }

        function getPredictabilityData(selectedWorkTypes, selectedProjectId, days, dateSince, dateUntil) {
            var workTypeStr = selectedWorkTypes.join();
            var predictabilityAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/' + 'throughput/' + 'predictability?';

            if (workTypeStr != '') predictabilityAPIStr += '&workTypes=' + workTypeStr;
            if (days) predictabilityAPIStr += '&days=' + days;
            if (dateSince) predictabilityAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) predictabilityAPIStr += '&dateUntil=' + dateUntil;

            var response = $http({
                method: 'GET',
                url: encodeURI(predictabilityAPIStr)
            });
            return response;
        }

        function getPRHistoryData(repoNameList, selectedProjectId, days, dateSince, dateUntil) {
            var historyStr = 'history';
            var historyAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/prs/' + 'throughput/' + historyStr + '?';

            if (days) historyAPIStr += '&days=' + days;
            if (dateSince) historyAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) historyAPIStr += '&dateUntil=' + dateUntil;
            if (repoNameList) historyAPIStr += '&repoName=' + repoNameList.join();

            var response = $http({
                method: 'GET',
                url: encodeURI(historyAPIStr)
            });
            return response;
        }

        function getPRStatisticsData(repoNameList, selectedProjectId, days, dateSince, dateUntil) {
            var statisticsStr = 'statistics';
            var statisticsAPIStr = routerConfig.apiGateway + 'project/' + selectedProjectId + '/prs/' + 'throughput/' + statisticsStr + '?';

            if (days) statisticsAPIStr += '&days=' + days;
            if (dateSince) statisticsAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) statisticsAPIStr += '&dateUntil=' + dateUntil;
            if (repoNameList) statisticsAPIStr += '&repoName=' + repoNameList.join();

            var response = $http({
                method: 'GET',
                url: encodeURI(statisticsAPIStr)
            });
            return response;
        }

        function getPRPredictabilityData(repoNameList, selectedProjectId, days, dateSince, dateUntil) {
            var predictabilityStr = 'predictability';
            var predictabilityAPIStr =
                routerConfig.apiGateway + 'project/' + selectedProjectId + '/prs/' +
                'throughput/' + predictabilityStr + '?';

            if (days) predictabilityAPIStr += '&days=' + days;
            if (dateSince) predictabilityAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) predictabilityAPIStr += '&dateUntil=' + dateUntil;
            if (repoNameList) predictabilityAPIStr += '&repoName=' + repoNameList.join();

            var response = $http({
                method: 'GET',
                url: encodeURI(predictabilityAPIStr)
            });
            return response;
        }

        function getPRLeadtimeData(repoNameList, selectedProjectId, days, dateSince, dateUntil) {
            var leadtimeStr = 'leadtime';
            var leadtimeAPIStr =
                routerConfig.apiGateway + 'project/' + selectedProjectId + '/prs/' + leadtimeStr + "?";

            if (days) leadtimeAPIStr += '&days=' + days;
            if (dateSince) leadtimeAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) leadtimeAPIStr += '&dateUntil=' + dateUntil;
            if (repoNameList) leadtimeAPIStr += '&repoName=' + repoNameList.join();

            var response = $http({
                method: 'GET',
                url: encodeURI(leadtimeAPIStr)
            });
            return response;
        }

        function getPRBacklogData(repoNameList, selectedProjectId, days, dateSince, dateUntil) {
            var backlogStr = 'backlog';
            var backlogAPIStr =
                routerConfig.apiGateway + 'project/' + selectedProjectId + '/prs/' + backlogStr + "?";

            if (days) backlogAPIStr += '&days=' + days;
            if (dateSince) backlogAPIStr += '&dateSince=' + dateSince;
            if (dateUntil) backlogAPIStr += '&dateUntil=' + dateUntil;
            if (repoNameList) backlogAPIStr += '&repoName=' + repoNameList.join();

            var response = $http({
                method: 'GET',
                url: encodeURI(backlogAPIStr)
            });
            return response;
        }
    }

    // Handles form input and retrieves info from AWS API gateway
    metricsFilterService.$inject = ['$http', 'routerConfig'];
    function metricsFilterService($http, routerConfig) {
        var service = {
            getTeams: getTeams,
            getAvailableTeams: getAvailableTeams,
            getProjects: getProjects,
            getWorkTypes: getWorkTypes,
        };
        
        return service;
        
        // Return list of teams
        // lambda function: /source/statistics/team.py
        function getTeams() {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'team/')
            });
            return response;
        }

        function getAvailableTeams() {
            var response = $http({
                method: 'GET',
                url: $rootScope.TEAM_LIST_API_ENDPOINT
            });
        }

        // Return list of projects
        // lambda function: /source/statistics/project.py
        function getProjects(teamId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'team/' + teamId + '/' + 'project/')
            });
            return response;
        }

        // Return list of worktypes
        // lamda function: /source/statistics/projectWorkTypes.py
        function getWorkTypes(projectId) {
            var response = $http({
                method: 'GET',
                url: encodeURI(routerConfig.apiGateway + 'project/' + projectId + '/'  + 'worktypes/')
            });
            return response;
        }
    }

})();
