angular.module('portal', [
  'ngAria',
  'ngMaterial',
  'ngMessages',
  'ngMdIcons',
  'ngResource',
  'ngSanitize',
  'ui.router',
  'vAccordion',
  'mdPickers',
  'bw.paging',
  'ui.select',
  'io.dennis.contextmenu',
  'lfNgMdFileInput'
])
  .factory('api', function($http, $q) {
    function get(model, filter){
      var defer = $q.defer();
      if (filter) {
        $http.get('/api/v1/import/' + model + '/?' + jQuery.param(filter)).
          success(function (data, status){
            defer.resolve({data: data, status: status});
          }).
          error(function (msg, status) {
            defer.resolve({msg: msg, status: status});
          });
      } else {
        $http.get('/api/v1/import/' + model + '/').
          success(function (data, status){
            defer.resolve({data: data, status: status});
          }).
          error(function (msg, status) {
            defer.resolve({msg: msg, status: status});
          });
      }
      return defer.promise
    }
    function post(model, data){
      var defer = $q.defer();
      $http.post('/api/v1/import/' + model + '/', data).
        success(function (data, status){
          defer.resolve({data: data, status: status});
        }).
        error(function (msg, status) {
          defer.resolve({msg: msg, status: status});
        });
      return defer.promise
    }
    function put(model, id, data) {
      var defer = $q.defer();
      $http.put('/api/v1/import/' + model + '/' + id + '/', data).
        success(function (data, status){
          defer.resolve({data: data, status: status});
        }).
        error(function (msg, status) {
          defer.resolve({msg: msg, status: status});
        });
      return defer.promise
    }
    return {
      get: get,
      post: post,
      put: put
    }
  })
  .controller('SchemaList', function($scope, api, $mdDialog){
    // $scope.object_list = {'name': 'default', 'id': 1};
    api.get('data_schema').then(function(resp){
      $scope.schema_list = resp.data.results;
    });
    $scope.$watch('files02.length',function(newVal,oldVal){
        console.log($scope.files02);
    });
    $scope.onFileClick = function(obj,idx){
        console.log(obj);
    };
    $scope.onFileRemove = function(obj,idx){
        console.log(obj);
    };
    $scope.openModal = function(ev, action, model) {
      if (model = 'update_schema'){
        api.get('schema_fields', {schema_id: $scope.import.schema}).then(function (resp) {
          $scope.field_list = resp.data.results;
        })
      }
      $mdDialog.show({
        controller: DialogController,
        templateUrl: '/static/js/' + action + '.html',
        parent: angular.element(document.body),
        targetEvent: ev,
        clickOutsideToClose:true,
        fullscreen: $scope.customFullscreen // Only for -xs, -sm breakpoints.
      })
      .then(function(answer) {
        $scope.status = 'You said the information was "' + answer + '".';
      }, function() {
        $scope.status = 'You cancelled the dialog.';
      });
    };
    function DialogController($scope, $mdDialog) {
      $scope.hide = function() {
        $mdDialog.hide();
      };

      $scope.cancel = function() {
        $mdDialog.cancel();
      };

      $scope.answer = function(answer) {
        $mdDialog.hide(answer);
      };
    }

  })
  .config(function($mdThemingProvider) {

    // Configure a dark theme with primary foreground yellow

    $mdThemingProvider.theme('docs-dark', 'default')
      .primaryPalette('yellow')
      .dark();

  });
