

/**
 * A referenced remote object.
 */
var ReferencedRemoteObject = (function($, infrae) {
    return function($widget, suffix) {
        // Refer a link that can represent a remote object on the
        // server. Its referenece (intid) can be store in a input called
        // widget_id-value.

        var identifier = $widget.attr('id');
        var url =  $widget.find('#' + identifier + '-base').val();
        var required_interface = $widget.find('#' + identifier + '-interface').val();
        var show_index = $widget.find('#' + identifier + '-show-index').val();
        var default_message = $widget.data('reference-default-message') || 'no reference selected.';
        var $container = $widget.find('ul.multiple-references');

        if (suffix) {
            identifier += suffix;
        };

        var $input = $widget.find('#' + identifier + '-value');
        var $link = $widget.find('#' + identifier + '-link');
        var $edit_link = $widget.find('#' + identifier + '-edit-link');

        if (!$link.length) {
            var $item = $('<li />');
            // XXX some class are missing here
            $link = $('<a id="' + identifier + '-link" />');
            $edit_link = $('<a id="' + identifier + '-edit-link" />');
            $item.append($link);
            $item.append($edit_link);
            $container.append($item);
        };

        var remote = {
            identifier: identifier + '-value',
            data: function() {
                // Return information to the remote object
                return $input.data('referenced-remote-content');
            },
            reference: function() {
                // Return reference (intid) to the remote object
                return $input.val();
            },
            title: function() {
                // Return title of the remote object
                var data = remote.data();

                if (data) {
                    return data['title'];
                };
                return 'no reference selected';
            },
            url: function() {
                // Return url of the remote object
                var data = remote.data();

                if (data) {
                    return data['url'];
                };
                return '';
            },
            clear: function(reason) {
                // Clear all value related to the remote object
                if (!reason) {
                    reason = default_message;
                };

                $edit_link.hide();
                $edit_link.attr('href', '#');
                $link.text(reason);
                $link.bind('click', function () { return false; });
                $link.attr('href', '#');
                $link.removeAttr('title');
                if ($input.length) {
                    $input.val('0');
                    $input.trigger('remote-reference-modified', {});
                };
            },
            fetch: function(intid) {
                // Fetch and render a object from its intid
                var options = {'intid': intid};

                $link.text('loading ...');
                if ($input.length)
                    $input.val(intid);

                if (required_interface)
                    options['interface'] = required_interface;
                if (show_index)
                    options['show_container_index'] = 'true';
                $.getJSON(url + '/++rest++silva.core.references.items', options, remote.render);
            },
            render: function(info) {
                if (info.url === undefined) {
                    remote.fetch(info.intid);
                    return;
                };
                // Render a link to a remote object from fetched information.
                var $icon = $('<ins class="icon" />');

                var set_or_remove_attr = function(name, value) {
                    if (value)
                        $link.attr(name, value);
                    else
                        $link.removeAttr(name);
                };

                $link.empty();
                $link.text(info['title']);
                set_or_remove_attr('href', info['url']);
                set_or_remove_attr('title', info['path']);
                $link.unbind('click');
                if (info['url']) {
                    $edit_link.show();
                    $edit_link.attr('href', info['path']);
                };
                $link.data('content', info);
                infrae.ui.icon($icon, info['icon']);
                $icon.prependTo($link);
                if ($input.length) {
                    $input.val(info['intid']);
                    $input.trigger('reference-modified', info);
                };
            },
            change: function(callback) {
                // Bind to a modification of the reference
                $input.bind('reference-modified', callback);
            },
            show: $widget.show,
            hide: $widget.hide,
            toggle: $widget.toggle
        };
        return remote;
    };
})(jQuery, infrae);
