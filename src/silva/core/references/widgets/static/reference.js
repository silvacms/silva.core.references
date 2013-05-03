
(function(infrae, $, jsontemplate) {
    var template = null;

    var get_template = function(url) {
        if (template !== null) {
            return $.when(template);
        };
        return $.ajax({
            url: url + '/++rest++silva.core.references.lookup'
        }).done(function (payload) {
            template = payload;
        });
    };

    var widget = {
        plugins: {},
        Manager: function($popup, configuration, smi) {
            // Screen stack.
            // stack: element 0 ContentList, element 1 Adder (if active)
            // XXX this stack is not the best for this
            var $current = undefined;
            var stack = [];
            var actions = [];
            var urls = [null];
            var manager = {
                configuration: $.extend({}, {
                    multiple : true,
                    show_index: false,
                    selected: []
                }, configuration),
                onchange: infrae.deferred.Callbacks()
            };

            // Open a url in a view
            var open_url = function(view, url) {
                return view.open(url).then(function (data) {
                    var index = urls.length - 1;
                    // The same url just have been added.
                    var added = index && urls[index] === null && urls[index - 1] == url;
                    if (added || (urls[index] !== url)) {
                        urls[index] = url;
                        if (!added) {
                            manager.onchange.invoke(manager, [url]);
                        };
                    }
                    return data;
                });
            };

            // Add a new view to the stack
            var open_view = function(view, url) {
                stack.push(view);
                urls.push(null);
                return open_url(view, url).done(function (data) {
                    // Insert the view.
                    $current = data.insert($current);
                    // Actions
                    if (data.actions !== undefined) {
                        actions.push($popup.dialog('option', 'buttons'));
                        $popup.dialog('option', 'buttons', data.actions);
                    };
                });
            };

            manager = $.extend(manager, {
                add: function(url, addable) {
                    var adder;

                    if (stack.length < 2) {
                        adder = infrae.smi.reference.Adder($popup, manager, smi, addable);
                        return open_view(adder, url);
                    };
                    adder = stack[1];
                    adder.update(addable);
                    return open_url(adder, url);
                },
                list: function(url) {
                    var listing;

                    if (!stack.length) {
                        listing = new infrae.smi.reference.Listing($popup, manager, smi);
                        return open_view(listing, url);
                    };
                    listing = stack[0];
                    return open_url(listing, url);
                },
                open: function(url) {
                    return open_url(stack[stack.length - 1], url);
                },
                back: function() {
                    if (stack.length > 1) {
                        var $old  = $current.prev();

                        $current.slideUp().promise(function () {$(this).remove();});
                        $old.slideDown();

                        $current = $old;
                        $popup.dialog('option', 'buttons', actions.pop());
                        stack.pop();

                        // Always refresh (for added content)
                        manager.open(urls.pop());
                    };
                }
            });

            // Load extensions
            for (var name in infrae.smi.reference.plugins) {
                infrae.smi.reference.plugins[name]($popup, manager);
            };
            return manager;
        }
    };

    $.extend(infrae.smi, {
        reference: widget
    });

    var create_reference_widget = function() {
        var $widget = $(this).parent('.reference-widget');
        var id = $widget.attr('id');
        var selected = [];
        var $value_input = $widget.find('#' + id + '-value');
        var $value_inputs = $widget.find('input[name="' + $value_input.attr('name') + '"]');
        var multiple = $value_input.hasClass('field-multiple');

        // Collect selected values
        $.each($value_inputs, function() {
            var value = $(this).val();
            if (value && value != '') {
                selected.push(value);
            }
        });

        var popup_buttons = {
            Cancel: function() {
                $(this).dialog('close');
            }
        };

        if (!$value_input.hasClass('field-required')) {
            popup_buttons['Clear'] = function() {
                var reference = ReferencedRemoteObject($widget);
                reference.clear();
                $(this).dialog('close');
            };
        };

        var url = $widget.find('#' + id + '-base').val();

        get_template(url).done(function(popup) {
            var $popup = $(popup);

            var manager = new widget.Manager(
                $popup,
                {multiple: multiple,
                 selected: selected,
                 show_index: $widget.find('#' + id + '-show-index').val(),
                 iface: $widget.find('#' + id + '-interface').val()},
                smi);

            if (multiple) {
                var items = [];

                $.each(selected, function(index, item) {
                    // Add stubs for already selected items;
                    items.push({intid: item});
                });
                $popup.bind('selected-smireferences', function(event, item) {
                    // An item is selected;
                    items.push(item);
                });
                $popup.bind('deselected-smireferences', function(event, item) {
                    // An item is unselected;
                    for (var i=0 ; i<items.length; i++) {
                        if (items[i].intid == item.intid) {
                            items.splice(i, 1);
                            break;
                        };
                    };
                });

                popup_buttons['Done'] = function(event) {
                    $.each($value_inputs, function() {
                        $(this).val('');
                    });
                    $widget.find('ul.multiple-references').empty();

                    $.each(items, function(index, item){
                        var suffix = index == 0 ? "" : String(index);
                        var $input = $value_inputs[index];
                        if ($input === undefined) {
                            $input = $value_input.clone();
                            $input.attr('id', id + suffix + "-value");
                            $input.appendTo($value_input.parent());
                        }
                        var reference = ReferencedRemoteObject($widget, suffix);
                        reference.render(item);
                    });
                    if ($value_inputs.length > 1) {
                        $.each($value_inputs, function() {
                            var $input = $(this);
                            if ($input.val() == '') {
                                $input.remove();
                            }
                        });
                    };
                    $popup.dialog('close');
                };
            } else {
                $popup.bind('selected-smireferences', function(event, item) {
                    var reference = ReferencedRemoteObject($widget);
                    reference.render(item);
                    $popup.dialog('close');
                });
            };
            $popup.bind('dialogclose', function() {
                $popup.remove();
            });

            // Create popup
            $popup.dialog({
                autoOpen: false,
                modal: true,
                height: 500,
                width: 800,
                zIndex: 12000,
                buttons: popup_buttons
            });
            manager.list(url);
            infrae.ui.ShowDialog($popup);
        });

        return false;
    };

    $.fn.SMIReferenceLookup = function() {
        $(this).delegate('.reference-dialog-trigger', 'click', create_reference_widget);
        return this;
    };

    $(document).on('loadwidget-smiform', '.form-fields-container', function(event) {
        $(this).delegate('.reference-dialog-trigger', 'click', create_reference_widget);
        event.stopPropagation();
    });

    $(document).ready(function() {
        $('.reference-dialog-trigger').bind('click', create_reference_widget);
    });

})(infrae, jQuery, jsontemplate);
