/*
 * AngularJS Main
 * Bundles the dependencies
 */

(function(){
    'use strict';

    // Dependencies
    var app = angular.module('vgerApp', [
        'ui.bootstrap',
        'googlechart',
        'angularjs-dropdown-multiselect',
        'angularSpinner',
        'dndLists',
        'ngMaterial',
        'ngMessages',
        'material.svgAssetsCache',
        'ngSanitize',
        'ngCsv',
        'vgerRouter',
        'vgerConstants',
        'componentConstants',
        'vgerMetricsController',
        'vgerMetricsService',
        'vgerDateController',
        'vgerDateService',
        'vgerFormsDirective',
        'vgerConfigurationsController',
        'vgerConfigurationsService',
        'vgerTooltipsDirective',
        'vgerDialogController',
        'vgerTeam',
        'vgerProject'
    ]);

})();
