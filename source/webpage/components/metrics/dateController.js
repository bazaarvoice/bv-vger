/*
 * Date helper functions
 */
 
(function(){
    'use strict';
    
    angular.module('vgerDateController', [])
    .controller('datePickerController', datePickerController);
    
    datePickerController.$inject = ['$scope', 'dateService', '$rootScope'];
    function datePickerController ($scope, dateService, $rootScope) {
        var vm = this; // view-model
        
        // Initialize default values
        if (!$rootScope.savedSearch) {
            dateService.setDateSince(new Date(new Date().setDate(new Date().getDate() - 90))); // o_o;;
            dateService.setDateUntil(new Date()); 
            dateService.setDays(90); // default interval of 90 days
        } 

        
        // Populate view-model
        vm.dateSince = dateService.getDateSince();
        vm.dateUntil = dateService.getDateUntil();
        vm.days = dateService.getDays();
        vm.error = false;
        vm.update = update;
        vm.dateChange = dateChange;
        vm.open1 = open1;
        vm.open2 = open2;
        vm.format = 'yyyy-MM-dd'
        vm.dateSinceOptions = {
            maxDate: new Date(dateService.getDateUntil().getTime() - (1000 * 60 * 60 * 24 * 14)) // subtract 14 days
        }
        vm.dateUntilOptions = {
            minDate: new Date(dateService.getDateSince().getTime() + (1000 * 60 * 60 * 24 * 14)), // add 14 days
            maxDate: new Date()
        }
        vm.popup1 = {
            opened: false
        };
        vm.popup2 = {
            opened: false
        };
        var daysBetween = daysBetween;
        
        // Helper function to control max/min date allowed while keeping the minimum interval to 14 days
        function dateChange(newDate, type) {
            vm.error = false; // reset and check for error again upon change
            if (type == 'dateSince') {
                if (newDate <= vm.dateSinceOptions.maxDate) {
                    dateService.setDateSince(newDate);
                    vm.dateUntilOptions.minDate = new Date(dateService.getDateSince().getTime() + (1000 * 60 * 60 * 24 * 14));
                } else {
                    vm.dateSince = dateService.getDateSince();  // out of range; correct it to original value
                }
            } else if (type == 'dateUntil') {
                if (newDate >= vm.dateUntilOptions.minDate && newDate <= vm.dateUntilOptions.maxDate) {
                    dateService.setDateUntil(newDate);
                    vm.dateSinceOptions.maxDate = new Date(dateService.getDateUntil().getTime() - (1000 * 60 * 60 * 24 * 14));
                } else {
                    vm.dateUntil = dateService.getDateUntil();  //out of range; correct to original value
                }
            } else if (type ==  'days') {
                if (newDate < 14) {
                    vm.error = true; // minimum 14 days interval 
                } 
                dateService.setDateSince(new Date(dateService.getDateUntil().getTime() - (1000 * 60 * 60 * 24 * newDate)));
                vm.dateSince = dateService.getDateSince();
                vm.dateUntilOptions.minDate = new Date(dateService.getDateSince().getTime() + (1000 * 60 * 60 * 24 * 14));
            }
            dateService.setDays(daysBetween(dateService.getDateSince(),dateService.getDateUntil()));
            vm.days = dateService.getDays();
            if (vm.days < 14) {
                vm.error = true;
            }
        }
        
        // dateSince popup
        function open1() {
            vm.popup1.opened = true;
        };
        
        // dateUntil popup
        function open2() {
            vm.popup2.opened = true;
        };
        
        function daysBetween(date1, date2) {
            var one_day=1000*60*60*24;                // Get 1 day in milliseconds
            var date1_ms = date1.getTime();           // Convert both dates to milliseconds
            var date2_ms = date2.getTime();
            var difference_ms = date2_ms - date1_ms;  // Calculate the difference in milliseconds
            return Math.round(difference_ms/one_day); // Convert back to days and return
        }
        
        function update() {
            vm.dateSince = dateService.getDateSince();
            vm.dateUntil = dateService.getDateUntil();
        }
    };
})();
