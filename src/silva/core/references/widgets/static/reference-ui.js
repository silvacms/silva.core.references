function indexFromId(data, id) {
    for(var i=0; i < data.length; i++) {
        if (data[i]['id'] == id) {
            return i;
        }
    }
    return null;
}

// defined a bind function if not exists
if (Function.prototype.scope === undefined) {
    Function.prototype.scope = function(scopearg) {
      var _function = this;

      return function() {
        return _function.apply(scopearg, arguments);
      };
    };
}

var Action = function(element, contentList) {
    this.event = 'click';
    this.element = $(element);
    this.link = $('button', this.element);
    this.contentList = contentList;
    this.enabled = true;
    this.link.bind(this.event, function(event){
        event.preventDefault();
        this.run(event);
    }.scope(this));
};

Action.prototype.run = function(event){ event.preventDefault(); };
Action.prototype.update = function(){};

Action.prototype.disable = function() {
    this.element.addClass('content-list-action-disabled');
    this.enabled = false;
};

Action.prototype.enable = function() {
    this.element.removeClass('content-list-action-disabled');
    this.enabled = true;
};

var Refresh = function(element, contentList) {
    Action.call(this, element, contentList);
    this.run = function() {
        if (this.enabled && this.contentList) {
            contentList.populate(this.contentList.url);
        }
    };
};

Refresh.prototype = new Action;


var Add = function(element, contentList) {
    Action.call(this, element, contentList);
    this.select = $('select', this.element);
    this.select.removeAttr('disabled');

    this.select.bind('change', function(event){
        event.preventDefault();
        this.run();
    }.scope(this));

    this.run = function() {
        if (this.enabled && this.contentList && this.contentList.current) {
            var url = this.contentList.current.url + '/edit/+/' +
                this.select.val();
            window.open(url);
        }
    };

    this.enable = function(){
        this.select.removeAttr('disabled');
        Action.prototype.enable.call(this);
    };

    this.disable = function() {
        this.select.attr('disabled', 'disabled');
        this.select.disabled = true;
        Action.prototype.disable.call(this);
    };

    this.update = function() {
        if (this.contentList && this.contentList.current) {
            var url = this.contentList.current.url + '/++rest++addables';
            var params = {};
            if (this.contentList.referenceInterface) {
                params['interface'] = this.contentList.referenceInterface;
            }
            this.disable();
            $.getJSON(url, params, function(data){
                this._updateAddables(data);
            }.scope(this));
        }
    };

    this._updateAddables = function(meta_types) {
        var option = $('option', this.select).first();
        this.select.empty();
        this.select.append(option);
        $.each(meta_types, function(index, item){
            var option = $('<option />');
            option.text(item);
            option.attr('value', item);
            option.appendTo(this.select);
        }.scope(this));
        this.enable();
    };

    this.update();
};

Add.prototype = new Action;


var ContentList = function(element, widgetId, options) {
    this.id = widgetId;
    this.element = $(element);
    this.referenceInterface = $('#' + this.id + '-interface').val();
    this.parent = null;
    this.current = null;
    this.selection = [];
    this.selectionIndex = {};
    this.actions = [];

    this.pathListElement = $('div.path-list', this.element);
    this.actionListElement = $('div.content-list-actions', this.element);
    this.listElement = $('table.source-list', this.element);
    this.selectionElement = $('table.selection-list', this.element);

    this.url = null;
    this.options = $.extend({'multiple' : false}, options);

    this.pathList = new PathList(this.pathListElement);

    this.bindActions();

    this.pathListElement.bind('path-modified', function(event, data){
        this.populate(data['url']);
    }.scope(this));

    if (this.options['multiple']) {
        var selectionView = new ContentListSelectionView(
            this.selectionElement, this);
        selectionView.render();
        this.element.append($('<h3>Selection</h3>'));
        this.element.append(this.selectionElement);
    }
};

ContentList.prototype.updateActions = function() {
    $.each(this.actions, function(index, action){
        action.update();
    });
};

ContentList.prototype.populate = function(url) {
    var options = {};

    if (this.referenceInterface) {
        options['interface'] = this.referenceInterface;
    };
    this.url = url;
    this.listElement.empty();

    $.getJSON(url + '/++rest++items', options, function(data) {
        this.listElement.empty();
        // get rid of '.' and '..'
        this.current = data[indexFromId(data, '.')];
        parent_id = indexFromId(data, '..');

        if (parent_id != null)
            this.parent = data.splice(parent_id, 1)[0];
        else
            this.parent = null;
        this.updateActions();
        view = new ContentListView(this.listElement, this);
        view.render(data);
    }.scope(this));
};

ContentList.prototype.buildPath = function() {
    this.pathList.fetch(this.current);
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
    this.element.trigger('content-list-item-selected', [item]);
    if (this.options.multiple) {
        var intid = item.info['intid'];
        this.selection.push(item);
        this.selectionIndex[item.info['intid']] = this.selection.length - 1;
        var view = new ContentListSelectionView(this.selectionElement, this);
        view.appendSelectionItem(item);
        var listitemview = new ContentListItemView(
            $('#' + this.itemDomId(item)), item);
        listitemview.disableSelectButton();
    }
};

ContentList.prototype.deselectItem = function(item) {
    var intid = item.info['intid'];
    var index = this.selectionIndex[intid];
    this.selection.splice(index, 1);
    delete this.selectionIndex[intid];

    this.element.trigger('content-list-item-deselected', [item]);
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

ContentList.prototype.bindActions = function() {
    var mapping = {
        'refresh': Refresh,
        'add': Add
    };

    $.each($('div.content-list-action', this.actionListElement),
                function(index, element) {
                    var wrapped = $(element);
                    var actionElement = $('button', wrapped);
                    var builder = mapping[actionElement.attr('name')];
                    if (builder) {
                        var action = new builder(wrapped, this);
                        this.actions.push(action);
                    }
                }.scope(this));
};

var ContentListView = function(element, contentList) {
    this.contentList = contentList;
    this.element = $(element);
};

ContentListView.prototype.render = function(data) {
    this.contentList.buildPath();
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
    view = new SelectionContentListItemView(element, item);
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
    var icon = $('<img />');
    var title_cell = $('<td class="cell_title" />');
    var link = null;

    if (this.item.info['folderish'] && !current) {
        this.element.addClass("folderish");
        id_cell.append($('<a href="#">' + this.item.info['id'] + "</a>"));
        link = $('<a href="#" />');
        this.element.click(function(event){
            this.item.contentList.populate(this.item.url);
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
            'src="../++resource++silva.core.references.widgets/add.png" />');
        img.click(function(event){
            this.item.contentList._itemClicked(event, this.item);
            event.stopPropagation();
        }.scope(this));
        actions_cell.append(img);
    }

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
        'src="../++resource++silva.core.references.widgets/delete.png" />');
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


var ReferencedRemoteObject = function(widget_id) {
    // Refer a link that can represent a remote object on the
    // server. Its referenece (intid) can be store in a input called
    // widget_id-value.
    this.id = widget_id;
    this.widget = $('#' + this.id);
    this.link = $('#' + this.id + '-link');
    this.edit_link = $('#' + this.id + '-edit-link');
    this.reference_input = $('#' + this.id + '-value');
    this.referenceInterface = $('#' + this.id + '-interface').val();
};

ReferencedRemoteObject.prototype.reference = function() {
    // Return reference (intid) to the remote object
    return this.reference_input.val();
};

ReferencedRemoteObject.prototype.data = function() {
    // Return information to the remote object
    return this.link.data('content');
};

ReferencedRemoteObject.prototype.title = function() {
    // Return title of the remote object
    var data = this.data();

    if (data) {
        return data['title'];
    }
    return 'no reference selected';
};


ReferencedRemoteObject.prototype.url = function() {
    // Return url of the remote object
    var data = this.data();

    if (data) {
        return data['url'];
    }
    return '';
};

ReferencedRemoteObject.prototype.clear = function(reason) {
    // Clear all value related to the remote object
    if (!reason) {
        reason = 'no reference selected';
    }
    this.edit_link.hide();
    this.edit_link.removeAttr('href');
    this.link.text(reason);
    this.link.bind('click', function () { return false; });
    this.link.removeAttr('href');
    this.link.removeAttr('title');
    if (this.reference_input) {
        this.reference_input.val('');
    };
    this.link.trigger('reference-modified', {});
};

ReferencedRemoteObject.prototype.fetch = function(intid) {
    // Fetch and render a object from its intid
    var url = $('#' + this.id + '-base').val();
    var options = {'intid': intid};

    this.link.text('loading ...');
    if (this.reference_input) {
        this.reference_input.val(intid);
    };
    if (this.referenceInterface) {
        options['interface'] = this.referenceInterface;
    };
    $.getJSON(url + '/++rest++items', options,
              function(data) {
                  this.render(data);
              }.scope(this));
};

ReferencedRemoteObject.prototype.render = function(info) {
    // Render a link to a remote object from fetched information.
    var icon = $('<img />');
    var set_or_remove_attr = function(name, value) {
        if (value) {
            this.link.attr(name, value);
        }
        else {
            this.link.removeAttr(name);
        };
    }.scope(this);

    this.link.empty();
    this.link.text(info['title']);
    set_or_remove_attr('href', info['url']);
    set_or_remove_attr('title', info['path']);
    this.link.unbind('click');
    if (info['url']) {
        this.edit_link.show();
        // XXX edit URL should come from data.
        this.edit_link.attr('href', info['url'] + '/edit');
    };
    this.link.data('content', info);
    icon.attr('src', info['icon']);
    icon.prependTo(this.link);
    if (this.reference_input) {
        this.reference_input.val(info['intid']);
    };
    this.link.trigger('reference-modified', info);
};

ReferencedRemoteObject.prototype.change = function(callback) {
    // Bind to a modification of the reference
    this.link.bind('reference-modified', callback);
};

ReferencedRemoteObject.prototype.show = function() {
    // Show widget
    this.widget.show();
};

ReferencedRemoteObject.prototype.hide = function() {
    // Hide widget
    this.widget.hide();
};

ReferencedRemoteObject.prototype.toggle = function() {
    // Hide/display widget
    this.widget.toggle();
};

var PathList = function(element, options) {
    this.element = $(element);
    default_options = {
    // link text
    'display_field': 'short_title',
    // link title attribute
    'title_field': 'id',
    // max items to display besides root
    'max_items': 3};
    options = options || {};
    this.options = {};
    $.extend(this.options, default_options, options);
};

PathList.prototype.fetch = function(info) {
    var url = info['url'];
    $.getJSON(url + '/++rest++parents',
                function(data) {
                    this.render(data);
                }.scope(this));
};

PathList.prototype.render = function(data) {
    var len = data.length;
    var max_items = this.options['max_items'];
    var stop = data.length;
    var start = 1;
    this.element.empty();
    this.element.append(this._build_entry(data[0]));

    if (max_items != 0 && len > (max_items + 1)) {
        start = len - max_items;
        this.element.append(this._build_fake());
    }

    for(var i = start; i < stop; i++) {
        this.element.append(this._build_entry(data[i]));
    }
};

PathList.prototype._build_fake = function() {
    var outer = $('<span class="path-outer" />');
    var inner = $('<span class="path-inner" />');
    // var img = $('<img />')
    var link = $('<span class="path-fake" />');
    link.text('...');
    link.appendTo(inner);
    inner.appendTo(outer);
    return outer;
};

PathList.prototype._build_entry = function(info) {
    var outer = $('<span class="path-outer" />');
    var inner = $('<span class="path-inner" />');
    var link = $('<a href="#" />');
    link.attr('title', info[this.options['title_field']]);
    link.text(info[this.options['display_field']]);
    link.data('++rest++', info);

    link.click(function(event){
        var data = $(event.target).data('++rest++');
        this._notify(event, data);
        return false;
    }.scope(this));

    link.appendTo(inner);
    inner.appendTo(outer);
    return outer;
};

PathList.prototype._notify = function(event, data) {
  this.element.trigger('path-modified', [data]);
};

$(document).ready(function() {

    $('.reference-dialog-trigger').live('click', function() {

        var widget_id = $(this).parent('.reference-widget').attr('id');
        var popup = $('#' + widget_id + '-dialog');

        var popup_buttons = {'cancel': function() {
            $(this).dialog('close');
        }};

        if (!$('#' + widget_id + '-value').hasClass('required')) {
            popup_buttons['clear'] = function(){
                var reference = new ReferencedRemoteObject(widget_id);
                reference.clear();
                $(this).dialog('close');
            };
        }

        popup.dialog({
            autoOpen: false,
            modal: true,
            height: 500,
            width: 600,
            buttons: popup_buttons
        });

        var url = $('#' + widget_id + '-base').val();
        var contentList = new ContentList(
            popup, widget_id, {'multiple': false});
        contentList.element.bind('content-list-item-selected',
            function(event, item) {
                var reference = new ReferencedRemoteObject(widget_id);
                reference.render(item.info);
                var popup = $('#' + widget_id + '-dialog');
                popup.dialog('close');
            });
        contentList.populate(url);
        popup.dialog('open');
        return false;
    });
});
