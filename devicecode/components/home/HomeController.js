app.controller('HomeController',
    function($scope, $timeout, $http) {

        $scope.updated = false;
        $scope.secondsAgo = 0;

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
                weightPerPill = 30,
                pressureThreshold = 200,
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
                if (target.weight === undefined) target.weight = source.weight;
                tmp = target.pillsRemaining;
                target.pillsRemaining = Math.floor(target.weight / weightPerPill);
                if (tmp != target.pillsRemaining) $scope.updated = true;

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
                    alert("Updated " + target.name);
                }

                updated[i] = target;
            }
       
            return updated;

        }


        poll();

    });
