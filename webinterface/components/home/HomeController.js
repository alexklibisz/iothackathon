app.controller('HomeController',
    function($scope, $timeout, $http) {

        $scope.person = {
            name: 'Leah R.'
        }

        $scope.data = {
            medications: []
        }

        var poll = function() {
            converting = true;
            var get = function() {
                $http.get('http://localhost:8000/data.json').success(function(data) {
                    $scope.data.medications = data;
                })
                $timeout(get, 1000);
                console.log("updated");
            }
            $timeout(get, 0);
        }

        poll();

    });
