// component constants for webpage
(function(){
	'use strict';

	angular.module('componentConstants', [])
    .service('constantsService', constantsService)

	constantsService.$inject = ['$rootScope']
	        
	function constantsService($rootScope){
		// const JIRA_SUPPORT_PROJECT_URL = ''
		const THROUGHPUT_README = "see external folder in gops-vger/docs"
		const BACKLOG_README = "see external folder in gops-vger/docs"
		const PR_GROWTH_README = "see external folder in gops-vger/docs"
		const THROUGHPUT_VARIATION_README = "see external folder in gops-vger/docs"
		const LEADTIMES_README = "see external folder in gops-vger/docs"
		const VGER_GUIDE = "see external folder in gops-vger/docs"					   
		// const BOARD_ID_URL = 'JIRAURL?rapidView='
		const ADD_PROJECT_URL = "see external folder in gops-vger/docs"
		const TEAM_LIST_API_ENDPOINT = 'API ENDPOINT WITH LIST OF TEAM NAMES'

		var service = {
            setRootScopeConstants: setRootScopeConstants,
        };
        
        return service;

		function setRootScopeConstants(){
			$rootScope.JIRA_SUPPORT_PROJECT_URL = JIRA_SUPPORT_PROJECT_URL;
			$rootScope.THROUGHPUT_README = THROUGHPUT_README;
			$rootScope.BACKLOG_README = BACKLOG_README;
			$rootScope.PR_GROWTH_README = PR_GROWTH_README;
			$rootScope.THROUGHPUT_VARIATION_README = THROUGHPUT_VARIATION_README;
			$rootScope.LEADTIMES_README = LEADTIMES_README;
			$rootScope.VGER_GUIDE = VGER_GUIDE;
			$rootScope.BOARD_ID_URL = BOARD_ID_URL;
			$rootScope.ADD_PROJECT_URL = ADD_PROJECT_URL;
			$rootScope.TEAM_LIST_API_ENDPOINT = TEAM_LIST_API_ENDPOINT;
		}

	}
})();


