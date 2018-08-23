(function(){
    'use strict';

    angular.module('vgerTooltipsDirective', [])
    .directive('tooltip', tooltip);

    // Custom directive to show tooltip metrics.html
    // hover over element to show info texts
    tooltip.$inject = [];
    function tooltip () {
        return {
            restrict: 'A',
            link: function(scope, element, attrs){
                $(element).hover(function(){
                    // on mouseenter
                    $(element).tooltip('show');
                }, function(){
                    // on mouseleave
                    $(element).tooltip('hide');
                });
            }
        };
    }
}()); 