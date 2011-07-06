

/**
 * A referenced remote object.
 */
var ReferencedRemoteObject = function(widget_id, suffix) {
    // Refer a link that can represent a remote object on the
    // server. Its referenece (intid) can be store in a input called
    // widget_id-value.

    var identifier = widget_id;
    var url =  $('#' + widget_id + '-base').val();
    var required_interface = $('#' + widget_id + '-interface').val();
    var $widget = $('#' + widget_id);

    if (suffix)
        identifier += suffix;

    var $input = $('#' + identifier + '-value');
    var $link = $('#' + identifier + '-link');
    var $edit_link = $('#' + identifier + '-edit-link');

    if (!$link.length) {
        var $container = $('#' + widget_id + ' ul.reference-links');
        var $item = $('<li />');
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

            if (data)
                return data['title'];
            return 'no reference selected';
        },
        url: function() {
            // Return url of the remote object
            var data = remote.data();

            if (data)
                return data['url'];
            return '';
        },
        clear: function(reason) {
            // Clear all value related to the remote object
            if (!reason)
                reason = 'no reference selected';

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
            $.getJSON(url + '/++rest++silva.core.references.items', options, remote.render);
        },
        render: function(info) {
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
                // XXX edit URL should come from data.
                $edit_link.attr('href', info['url'] + '/edit');
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

(function($) {
    // Top level add support
    $('.reference-dialog').live('load-smireferences', function () {
        var $popup = $(this);
        var $action = $popup.find('.content-list-action-add');
        var $trigger = $action.find('a');
        var $select = $action.find('select');
        var empty = $select.html();
        var url = null;

        var open = function() {
            $popup.trigger('add-smireferences', {url: url, addable: $select.val()});
            return false;
        };

        $trigger.bind('click', open);
        $select.bind('change', open);

        $popup.bind('change-smireferences', function (event, data) {
            // The selected container changed, update the add menu
            url = data['url'];

            $.ajax({
                url: url + '/++rest++silva.core.references.addables',
                dataType: 'json'
            }).done(function(addables) {
                var options = [empty];

                for (var i=0, len=addables.length; i < len; i++) {
                    options.push('<option value="' + addables[i] + '">' + addables[i] + '</option>');
                };
                $select.html(options.join(''));
            });
        });
    });

    // Top level path breadcrumb
    var breadcrumb_template = new jsontemplate.Template('<span class="path-outer"><span class="path-inner">{.section link}<a href="{url|html-attr-value}" title="{id|html-attr-value}">{short_title|html}</a>{.end}{.section last}<span class="last">{short_title|html}</span>{.end}</span>{.section separator}<span class="separator">&rsaquo;</span>{.end}</span>');

    $('.reference-dialog').live('load-smireferences', function () {
        var $popup = $(this);
        var $breadcrumb = $popup.find('.path-list');

        // Open a container if you click on it
        $breadcrumb.delegate('a', 'click', function(event) {
            $popup.trigger('open-smireferences', {url: $(event.target).attr('href')});
            return false;
        });

        $popup.bind('change-smireferences', function (event, data) {
            // The selected container changed, update the breadcrumb
            $.ajax({
                url: data['url'] + '/++rest++silva.core.references.parents',
                dataType: 'json'
            }).done(function(parents) {
                var len = parents.length;
                var max_items = 3;
                var position = 1;
                var parts = [];

                var build = function(info, last) {
                    return breadcrumb_template.expand({
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
    });
})(jQuery);

(function($) {

    var Manager = function($popup, smi, id, options) {
        // Load extensions
        $popup.trigger('load-smireferences');

        // Load system
        var stack = [new ContentList($popup, smi, id, options)];
        var actions = [];
        var urls = [];
        var $current = $popup.find('.content-list');

        // Open a url in a view
        var open_url = function(view, url) {
            return view.open(url).pipe(function (data) {
                urls[urls.length - 1] = url;
                $popup.trigger('change-smireferences', {url: url});
                return data;
            });
        };

        // Add a new view to the stack
        var new_view = function(view, url) {
            stack.push(view);
            return open_url(view, url).done(function (data) {
                var $new = data.$content;

                $new.hide();
                $new.insertAfter($current);
                $current.slideUp();
                $new.slideDown();
                $current = $new;

                // Actions
                actions.push($popup.dialog('option', 'buttons'));
                $popup.dialog('option', 'buttons', data.actions);

                // Url safety
                urls.push(url);
            });
        };

        var manager = {
            add: function(url, addable) {
                var adder = Adder($popup, smi, addable);
                return new_view(adder, url);
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
                }
            }
        };

        // Bind events for extensions
        $popup.bind('open-smireferences', function(event, data) {
            manager.open(data.url);
        });
        $popup.bind('add-smireferences', function(event, data) {
            manager.add(data.url, data.addable);
        });
        $popup.bind('back-smireferences', function(event, data) {
            manager.back();
        });
        return manager;
    };

    var Adder = function($popup, smi, addable) {
        var $content = $('<div />');
        var $form = null;

        return {
            open: function(url) {
                var form_url = url + '/++rest++silva.core.references.adding/' + addable;

                var render_form = function(data) {
                    $content.html(data.screen.forms);
                    $form = $content.children('form');
                    $form.attr('data-form-url', form_url);
                    $form.trigger('load-smiform');
                    return {
                        $content: $content,
                        actions: {
                            Back: function() {
                                $popup.trigger('back-smireferences');
                            },
                            Add: function() {
                                var values = $form.serializeArray();
                                values.push({
                                    name: $form.attr('name') + '.action.save',
                                    value: 'Save'});
                                smi.ajax.query(form_url, values).pipe(function (data) {
                                    // The add form redirect on success.
                                    if (infrae.interfaces.isImplementedBy('redirect', data)) {
                                        $popup.trigger('back-smireferences');
                                    } else {
                                        render_form(data);
                                    };
                                });
                            }
                        }
                    };
                };

                return smi.ajax.query(form_url).pipe(render_form);
            }
        };
    };

    // defined a bind function if not exists
    if (Function.prototype.scope === undefined) {
        Function.prototype.scope = function(scopearg) {
            var _function = this;

            return function() {
                return _function.apply(scopearg, arguments);
            };
        };
    };

    function indexFromId(data, id) {
        for(var i=0; i < data.length; i++) {
            if (data[i]['id'] == id) {
                return i;
            }
        }
        return null;
    };

    var ContentList = function(element, smi, widgetId, options) {
        this.id = widgetId;
        this.element = $(element);
        this.referenceInterface = $('#' + this.id + '-interface').val();
        this.parent = null;
        this.current = null;
        this.selection = [];
        this.selectionIndex = {};

        var defaults = {'multiple' : true, 'selected': []};

        this.listElement = $('table.source-list', this.element);
        this.selectionElement = $('table.selection-list', this.element);

        this.url = null;
        this.options = $.extend(defaults, options);

        if (this.options['multiple']) {
            var selectionView = new ContentListSelectionView(
                this.selectionElement, this);
            selectionView.render();
        }

        if (this.options['multiple'] && this.options['selected'].length > 0) {
            $.each(this.options['selected'], function(index, selected) {
                var url = '++rest++silva.core.references.items';
                $.getJSON(url, {'intid': selected}, function(entry) {
                    var item = new ContentListItem(this,
                                                   this.url + '/' + entry['id'], entry);
                    this.selectItem(item);
                }.scope(this));
            }.scope(this));
        }
        if (this.options['multiple']) {
            this.selectionElement.show();
        } else {
            this.selectionElement.hide();
        }
    };

    ContentList.prototype.open = function(url) {
        var options = {url: url + '/++rest++silva.core.references.items'};

        if (this.referenceInterface) {
            options['data'] = {'interface': this.referenceInterface};
        };
        this.url = url;
        this.listElement.empty();

        return $.ajax(options).pipe(function(data) {
            this.listElement.empty();
            // get rid of '.' and '..'
            this.current = data[indexFromId(data, '.')];
            var parent_id = indexFromId(data, '..');

            if (parent_id != null)
                this.parent = data.splice(parent_id, 1)[0];
            else
                this.parent = null;
            var view = new ContentListView(this.listElement, this);
            view.render(data);
            return {};
        }.scope(this));
    };

    ContentList.prototype.itemDomId = function(item) {
        return 'list-item-' + item.info['intid'];
    };

    ContentList.prototype._itemClicked = function(event, item) {
        if (this.isSelected(item)) {
            this.deselectItem(item);
        } else {
            this.selectItem(item);
        }
    };

    ContentList.prototype._itemRemovedFromSelection = function(event, item) {
        this.deselectItem(item);
    };

    ContentList.prototype.selectItem = function(item) {
        this.element.trigger('selected-smireferences', [item]);
        if (this.options.multiple) {
            var intid = item.info['intid'];
            this.select(item);
            var view = new ContentListSelectionView(this.selectionElement, this);
            view.appendSelectionItem(item);
            var listitemview = new ContentListItemView(
                $('#' + this.itemDomId(item)), item);
            listitemview.disableSelectButton();
        }
    };

    ContentList.prototype.select = function(item) {
        this.selection.push(item);
        this.selectionIndex[item.info['intid']] = this.selection.length - 1;
    };

    ContentList.prototype.deselectItem = function(item) {
        var intid = item.info['intid'];
        var index = this.selectionIndex[intid];
        this.selection.splice(index, 1);
        delete this.selectionIndex[intid];

        this.element.trigger('deselected-smireferences', [item]);
        var selview = new ContentListSelectionView(this.selectionElement, this);
        selview.removeSelectionItem(item);
        var listitemview = new ContentListItemView(
            $('#' + this.itemDomId(item)), item);
        listitemview.enableSelectButton();
    };

    ContentList.prototype.isSelected = function(item) {
        var intid = item.info['intid'];
        var index = this.selectionIndex[intid];
        if (index >= 0)
            return true;
        return false;
    };

    var ContentListView = function(element, contentList) {
        this.contentList = contentList;
        this.element = $(element);
    };

    ContentListView.prototype.render = function(data) {
        $.each(data, function(index, entry) {
            var child = new ContentListItem(
                this.contentList,
                this.contentList.url + '/' + entry['id'], entry);
            var childElement = $('<tr />');
            childElement.attr('id', this.contentList.itemDomId(child));
            childElement.addClass(index % 2 ? "even" : "odd");
            var childView = new ContentListItemView(childElement, child);
            childView.render();
            if (this.contentList.isSelected(child))
                childView.disableSelectButton();
            this.element.append(childElement);
        }.scope(this));
    };

    var ContentListSelectionView = function(element, contentList) {
        this.element = $(element);
        this.contentList = contentList;
    };

    ContentListSelectionView.prototype.appendSelectionItem = function(item) {
        var element = $('<tr />');
        var view = new SelectionContentListItemView(element, item);
        view.render();
        element.attr('id', this.itemDomId(item));
        this.element.append(element);
    };

    ContentListSelectionView.prototype.removeSelectionItem = function(item) {
        $('#' + this.itemDomId(item)).remove();
    };

    ContentListSelectionView.prototype.render = function(item) {
        this.element.empty();
        for(var i=0; i < this.contentList.selection.length; i++) {
            this.appendSelectionItem(this.contentList.selection[i]);
        }
    };

    ContentListSelectionView.prototype.itemDomId = function(item) {
        return 'selection-item-' + item.info['intid'];
    };

    var ContentListItem = function(
        contentList, url, info) {
        this.contentList = contentList;
        this.url = url;
        this.info = info;
    };

    var ContentListItemView = function(element, item) {
        this.item = item;
        this.element = $(element);
    };

    ContentListItemView.prototype.disableSelectButton = function() {
        this.getSelectButton().hide();
    };

    ContentListItemView.prototype.enableSelectButton = function() {
        this.getSelectButton().show();
    };

    ContentListItemView.prototype.getSelectButton = function() {
        return this.element.find('td.cell_actions .reference_add');
    };

    ContentListItemView.prototype.render = function() {
        this.element.empty();
        var current = (this.item.info['id'] == '.');
        var icon_cell = $('<td class="cell_icon" />');
        var actions_cell = $('<td class="cell_actions" />');
        var id_cell = $('<td class="cell_id" />');
        var $icon = $('<ins class="icon" />');
        var title_cell = $('<td class="cell_title" />');
        var link = null;

        if (this.item.info['folderish'] && !current) {
            this.element.addClass("folderish");
            id_cell.append($('<a href="#">' + this.item.info['id'] + "</a>"));
            link = $('<a href="#" />');
            this.element.click(function(event){
                this.item.contentList.element.trigger(
                    'open-smireferences', {url: this.item.url});
                return false;
            }.scope(this));
            this.element.hover(function(event){
                // in
                $(this).addClass('folderish-hover');
            }, function(event){
                // out
                $(this).removeClass('folderish-hover');
            });
        } else {
            if (current) {
                this.element.addClass('current');
                id_cell.text('current location');
            } else {
                id_cell.text(this.item.info['id']);
            }
            link = $('<span />');
        }

        if (this.item.info['implements']) {
            var img = $('<img class="button reference_add"' +
                        'src="++static++/silva.core.references.widgets/add.png" />');
            img.click(function(event){
                this.item.contentList._itemClicked(event, this.item);
                event.stopPropagation();
            }.scope(this));
            actions_cell.append(img);
        }

        link.data('++rest++', this.item.info);
        link.text(this.item.info['title']);
        link.appendTo(title_cell);

        infrae.ui.icon($icon, this.item.info['icon']);
        $icon.appendTo(icon_cell);

        icon_cell.appendTo(this.element);
        title_cell.appendTo(this.element);
        id_cell.appendTo(this.element);
        actions_cell.appendTo(this.element);
    };

    var SelectionContentListItemView = function(element, item) {
        this.item = item;
        this.element = $(element);
    };

    SelectionContentListItemView.prototype.render = function() {
        var icon_cell = $('<td class="cell-icon" />');
        var actions_cell = $('<td class="cell-actions" />');
        var id_cell = $('<td class="cell-id" />');
        var icon = $('<img />');
        var title_cell = $('<td class="cell-title" />');
        var link = $('<span />');;

        var removeButton = $('<img class="button reference_remove"' +
                             'src="++static++/silva.core.references.widgets/delete.png" />');
        removeButton.click(function(event){
            this.item.contentList._itemRemovedFromSelection(event, this.item);
        }.scope(this));
        actions_cell.append(removeButton);

        id_cell.text(this.item.info['path']);

        link.data('++rest++', this.item.info);
        link.text(this.item.info['title']);
        link.appendTo(title_cell);

        icon.attr('src', this.item.info['icon']);
        icon.attr('title', this.item.info['type']);
        icon.appendTo(icon_cell);

        icon_cell.appendTo(this.element);
        title_cell.appendTo(this.element);
        id_cell.appendTo(this.element);
        actions_cell.appendTo(this.element);
    };

    var popup_template = null;

    var get_popup_template = function(url) {
        if (popup_template !== null) {
            return $.when(popup_template);
        };
        return $.ajax({url: url + '/++rest++silva.core.references.lookup'}).done(function (payload) {
            popup_template = payload;
        });
    };

    $(document).bind('load-smiplugins', function(event, smi) {

        $('.reference-dialog-trigger').live('click', function() {
            var widget_id = $(this).parent('.reference-widget').attr('id');
            var widget = $('#' + widget_id);
            var value_input = $('#' + widget_id + '-value');
            var value_inputs = $('input[name="' + value_input.attr('name') + '"]', widget);
            var selected = [];
            var multiple = value_input.hasClass('multiple');

            $.each(value_inputs, function() {
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

            if (!value_input.hasClass('field-required')) {
                popup_buttons['Clear'] = function(){
                    var reference = ReferencedRemoteObject(widget_id);
                    reference.clear();
                    $(this).dialog('close');
                };
            };

            var url = $('#' + widget_id + '-base').val();

            get_popup_template(url).done(function(popup) {
                var $popup = $(popup);

                // Create popup
                $popup.dialog({
                    autoOpen: false,
                    modal: true,
                    height: 500,
                    width: 800,
                    zIndex: 12000,
                    buttons: popup_buttons
                });
                $popup.bind('dialogclose', function() {
                    $popup.remove();
                });

                var manager = new Manager(
                    $popup, smi, widget_id,
                    {'multiple': multiple, 'selected': selected});

                if (multiple) {
                    popup_buttons['Done'] = function(event){
                        // XXX Do something with selection
                        value_inputs =
                            $('input[name="' + value_input.attr('name') + '"]',
                              widget);
                        $.each(value_inputs, function(index, input){
                            $(input).val('');
                        });
                        $('ul.reference-links',  widget).empty();
                        $.each(contentList.selection, function(index, item){
                            var suffix = index == 0 ? "" : String(index);
                            var input = value_inputs[index];
                            if (input === undefined) {
                                input = value_input.clone();
                                input.attr('id', widget_id + suffix + "-value");
                                input.appendTo(value_input.parent());
                            }
                            var reference = ReferencedRemoteObject(widget_id, suffix);
                            reference.render(item.info);
                        });
                        if (value_inputs.length > 1) {
                            $.each(value_inputs, function(index, input){
                                var $input = $(input);
                                if ($input.val() == '') {
                                    $input.remove();
                                }
                            });
                        }
                        $popup.dialog('close');
                    };
                } else {
                    $popup.bind('selected-smireferences', function(event, item) {
                        var reference = ReferencedRemoteObject(widget_id);
                        reference.render(item.info);
                        $popup.dialog('close');
                    });
                };

                manager.open(url);
                $popup.dialog('open');
            });
            return false;
        });
    });


})(jQuery);

