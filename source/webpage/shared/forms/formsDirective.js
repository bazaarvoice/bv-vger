(function(){
    'use strict';

    angular.module('vgerFormsDirective', [])
    .directive('selectOnClick', selectOnClick);

    // Custom directive to filter forms in metrics.html
    // selectOnClick: highlight(select-all) the input field on click
    selectOnClick.$inject = ['$window'];
    function selectOnClick ($window) {
        // Linker function
        return function (scope, element, attrs) {
            element.bind('click', function () {
                if (!$window.getSelection().toString()) {
                    this.setSelectionRange(0, this.value.length);
                }
            });
        };
    }
}()); 