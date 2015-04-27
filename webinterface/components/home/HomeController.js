/**
 * The primary application logic.
 * Uses the function poll() to retrieve the data.json file every 2 seconds.
 * poll() calls parseData() to convert the data to a usable format.
 *
 * It's rough, but works.
 */
app.controller('HomeController',
    function($scope, $timeout, $http) {

        $scope.updated = false;

        $scope.person = {
            name: 'Jane Doe'
        }

        $scope.data = {
            meds: []
        }

        var poll = function() {
            converting = true;
            var get = function() {
                $http.get('http://localhost:8000/data.json').success(function(data) {
                    $scope.data.meds = parseData(data);
                })
                $timeout(get, 2000);
            }
            $timeout(get, 0);
        }

        /**
         * data will contain a weight and a pressure reading
         * for each medication
         *
         * each object in the updated list should have a 
         * name, timeTaken, pillsRemaining, estimatedRefillDate
         */
        var parseData = function(data) {
            var updated = $scope.data.meds,
                weightPerPill = 75,
                weightThreshold = 750,
                pressureThreshold = 40,
                pillsPerDay = 2;

            $scope.updated = false;

            for (var i = 0; i < data.length; i++) {
                var source = data[i],
                    target, tmp;

                if ($scope.data.meds.length === 0) {
                    target = {};
                } else {
                    target = $scope.data.meds[i];
                }

                // get the name, just in case it changed
                target.name = source.name;

                // convert the weight to pillsRemaining
                if (target.weight === undefined) target.weight = source.weight - weightThreshold;
                target.weight = source.weight - weightThreshold;
                tmp = target.pillsRemaining;
                target.pillsRemaining = Math.floor(target.weight / weightPerPill);
                if (tmp != target.pillsRemaining) $scope.updated = true;
                //$scope.pillsRemaining = target.pillsRemaining;

                if(target.timeTaken === undefined) target.timeTaken = new Date();
                // check the pressure to update the timeTaken
                if (source.pressure < pressureThreshold
                    && target.pressure !== source.pressure) {
                    target.pressure = source.pressure;
                    target.timeTaken = new Date();
                    $scope.updated = true;
                }

                // update the estimatedRefill
                var daysRemaining = Math.floor(target.pillsRemaining / pillsPerDay);
                target.estimatedRefill = new Date();
                target.estimatedRefill.setDate((new Date()).getDate() + daysRemaining);

                if($scope.updated) {
                    alert("Updated medication: " + target.name);
                }

                updated[i] = target;
            }
            return updated;
        }

        poll();

    });
