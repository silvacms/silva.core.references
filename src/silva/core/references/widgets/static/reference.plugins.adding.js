
(function(infrae, $, jsontemplate) {

    $.extend(infrae.smi.reference.plugins, {
        AddMenu: function($popup, manager) {
            var $action = $popup.find('.content-actions');
            var $trigger = $action.find('a');
            var $select = $action.find('select');
            var empty = $select.html();
            var opened_url = null;

            var open = function() {
                var selected = $select.val();
                if (selected && opened_url) {
                    manager.add(opened_url, selected);
                };
                return false;
            };

            $trigger.bind('click', open);
            $select.bind('change', open);

            manager.onchange.add(function (url) {
                // The selected container changed, update the add menu
                var options = {
                    url: url + '/++rest++silva.core.references.adding',
                    dataType: 'json'
                };
                if (manager.configuration.iface !== undefined) {
                    options['data'] = {'interface': manager.configuration.iface};
                };

                $.ajax(options).done(function(addables) {
                    var options = [empty];

                    $action.toggle(addables.length !== 0);
                    for (var i=0, len=addables.length; i < len; i++) {
                        options.push('<option value="' + addables[i] + '">' + addables[i] + '</option>');
                    };
                    opened_url = url;
                    $select.html(options.join(''));
                });
            });
        }
    });

})(infrae, jQuery, jsontemplate);
