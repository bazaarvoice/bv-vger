/*
 * Navigation helper built with ui-router
 * Renders appropriate html file to ui-view directive in index.html
 */

(function(){
    'use strict';

    var app = angular.module('vgerRouter', ['ui.router']);
    app.config(function($stateProvider, $urlRouterProvider, $httpProvider) {

        $urlRouterProvider.otherwise('/team');

        $stateProvider
        // Metrics quadrant
        .state('metrics', {
            url: '/metrics',
            templateUrl: 'components/metrics/metrics.html'
        })
        
        // Create team
        .state('team', {
            url: '/team',
            templateUrl: 'components/team/team.html'
        })
        
        // Create project
        .state('project', {
            url: '/project',
            templateUrl: 'components/project/project.html'
        })

        // View reports
        .state('reports', {
            url: '/reports',
            templateUrl: '/reports/build/index.html'
        })
        
        // Prevents browser from sending preflight OPTIONS requests before POST/PUT
        $httpProvider.defaults.headers.common = {};
        $httpProvider.defaults.headers.post = {};
        $httpProvider.defaults.headers.put = {};
        $httpProvider.defaults.headers.patch = {};
    });    
})();
