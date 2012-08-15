(function(infrae, $, jsontemplate) {

    var template = new jsontemplate.Template('<span class="path-outer"><span class="path-inner">{.section link}<a href="{url|html-attr-value}" title="{id|html-attr-value}">{short_title|html}</a>{.end}{.section last}<span class="last">{short_title|html}</span>{.end}</span>{.section separator}<span class="separator">&rsaquo;</span>{.end}</span>');
    var max_items = 3;

    $.extend(infrae.smi.reference.plugins, {
        Breadcrumbs: function($popup, manager) {
            var $breadcrumb = $popup.find('.path-list');

            // Open a container if you click on it
            $breadcrumb.delegate('a', 'click', function(event) {
                manager.open($(event.target).attr('href'));
                return false;
            });

            manager.onchange.add(function (url) {
                // The selected container changed, update the breadcrumb
                $.ajax({
                    url: url + '/++rest++silva.core.references.parents',
                    dataType: 'json'
                }).done(function(parents) {
                    var len = parents.length;
                    var position = 1;
                    var parts = [];

                    var build = function(info, last) {
                        return template.expand({
                            separator: !last,
                            last: last && info,
                            link: (!last) && info
                        });
                    };

                    // First part
                    parts.push(build(parents[0], 1 == len));
                    // Skip some if there are lot of those
                    if (max_items != 0 && len > (max_items + 1)) {
                        position = len - max_items;
                        parts.push('<span class="path-outer">' +
                                   '<span class="path-inner">' +
                                   '<span class="path-fake">...</span>' +
                                   '</span>' +
                                   '<span class="separator">&rsaquo;</span>' +
                                   '</span>');
                    }
                    // Add the leftover
                    for(; position < len; position++) {
                        parts.push(build(parents[position], position + 1 == len));
                    }
                    $breadcrumb.html(parts.join(''));
                });
            });
        }
    });

})(infrae, jQuery, jsontemplate);
