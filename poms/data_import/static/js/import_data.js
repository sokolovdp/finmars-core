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
    function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
              var cookie = jQuery.trim(cookies[i]);
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
    }
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
      $http.post('/api/v1/import/' + model + '/', data, {headers: {'X-CSRFToken': getCookie('csrftoken')}}).
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
  .controller('SchemaList', function($scope, api, $mdDialog, $filter){
    // $scope.object_list = {'name': 'default', 'id': 1};
    api.get('data_schema').then(function(resp){
      $scope.schema_list = resp.data.results;
    });

    $scope.update = function () {
      $scope.selectedItem = $filter('filter')($scope.schema_list, {id: parseInt($scope.import.schema)}, true)[0];
    };
    $scope.openModal = function(ev, action, model) {
      if (model = 'update_schema'){
        api.get('schema_fields', {schema_id: $scope.selectedItem.id}).then(function (resp) {
          $scope.field_list = resp.data.results;
          $mdDialog.show({
            controller: DialogController,
            templateUrl: '/static/js/' + action + '.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            clickOutsideToClose:true,
            fullscreen: $scope.customFullscreen,
            locals : {
                schema: $scope.selectedItem,
                field_list: $scope.field_list
            }
          })
          .then(function(answer) {
            $scope.status = 'You said the information was "' + answer + '".';
          }, function() {
            $scope.status = 'You cancelled the dialog.';
          });
        });
      }
    };
    function DialogController($scope, $mdDialog, api, schema, field_list) {
      $scope.schema = schema;
      $scope.field_list = field_list;
      api.get('schema_models').then(function (resp) {
        $scope.models = resp.data.results;
      });
      $scope.copyField = function(){
        $scope.field_list.push({num: 0, source: 'source', target: 'target', schema: schema.id});
      };
      $scope.removeField = function(item, index){
        $scope.field_list.splice(index, 1);
      };
      $scope.saveSchema = function(){
        api.put('schema_fields', $scope.field_list).then(function(resp){
          console.log(resp);
          $scope.hide()
        });
      };
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
    $mdThemingProvider.theme('docs-dark', 'default')
      .primaryPalette('yellow')
      .dark();

  });
