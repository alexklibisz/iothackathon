app.controller('HomeController',
    function($scope, $timeout) {

        $scope.person = {
            name: 'Leah R.'
        }

        var date = new Date();

        $scope.data = {
            medications: [{
                'name': 'Medicine p',
                'timeTaken': new Date(),
                'pillsRemaining': 5,
                'estimatedRefill': new Date()
            }, {
                'name': 'Medicine 2',
                'timeTaken': new Date(),
                'pillsRemaining': 3,
                'estimatedRefill': new Date()
            }, {
                'name': 'Medicine 3',
                'timeTaken': new Date(),
                'pillsRemaining': 6,
                'estimatedRefill': new Date()
            }]
        }
    });
