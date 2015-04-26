app.controller('HomeController',
    function($scope, $timeout, $http) {

        $scope.person = {
            name: 'Leah R.'
        }

        $scope.data = {
            medications: []
        }

        $scope.test = function() {
            $scope.data.medications[0].pillsRemaining = Math.floor((Math.random() * 10) + 1);
            $scope.data.medications[1].pillsRemaining = Math.floor((Math.random() * 10) + 1);
            $scope.data.medications[2].pillsRemaining = Math.floor((Math.random() * 10) + 1);
        }

        $http.get('http://localhost:8000/data.json').success(function(data) {
            $scope.data.medications = data;
        })
    });
