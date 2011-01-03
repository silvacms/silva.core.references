var ContentList = function(element, widget_id, options) {
    this.id = widget_id;
    this.element = $(element);
    this.element.empty();
    this.reference_interface = $('#' + this.id + '-interface');
    this.parent = null;
    this.current = null;
    this.selection = [];
    this.selectionIndex = {};
    this.pathListElement = $('<div class="path_list" />');
    this.actionListElement = $('<div class="content-list-actions">');
    this.listElement = $('<table class="content_list" />');
    this.selectionElement = $('<table class="content_list selection_list">');
    this.url = null;
    this.options = $.extend({'multiple' : true}, options);
    this.pathList = new PathList(this.pathListElement);

    var self = this;

    this.pathList.element.bind('path-modified', function(event, data){
        self.populate.apply(self, [data['url']]);
    });

    this.element.append(this.pathListElement);
    this.element.append(this.actionListElement)
    this.element.append(this.listElement);
    if (this.options['multiple']) {
        var selectionView = new ContentListSelectionView(
            this.selectionElement, this);
        selectionView.render();
        this.element.append($('<h3>Selection</h3>'));
        this.element.append(this.selectionElement)
    }
};

function index_from_id(data, id) {
    for(var i=0; i < data.length; i++) {
        if (data[i]['id'] == id) {
            return i;
        }
    }
    return null;
}


ContentList.prototype.populate = function(url) {
    var self = this;
    var options = {};

    if (this.reference_interface.val()) {
        options['interface'] = this.reference_interface.val();
    };
    this.url = url;
    $.getJSON(url + '/++rest++items', options, function(data) {
        self.listElement.empty();
        // get rid of '.' and '..'
        self.current = data[index_from_id(data, '.')];
        parent_id = index_from_id(data, '..');

        if (parent_id != null)
            self.parent = data.splice(parent_id, 1)[0];
        else
            self.parent = null;
        view = new ContentListView(self.listElement, self);
        view.render(data);
    });
};

ContentList.prototype.build_path = function() {
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
    var intid = item.info['intid'];
    this.selection.push(item);
    this.selectionIndex[item.info['intid']] = this.selection.length - 1;

    this.element.trigger('content-list-item-selected', [item]);
    var view = new ContentListSelectionView(this.selectionElement, this);
    view.appendSelectionItem(item);
    var listitemview = new ContentListItemView(
        $('#' + this.itemDomId(item)), item);
    listitemview.disableSelectButton();
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

var ContentListView = function(element, contentList) {
    this.content_list = contentList;
    this.element = $(element);
};

ContentListView.prototype.render = function(data) {
    var self = this;
    this.content_list.build_path();
    this.buildActions();
    $.each(data, function(index, entry) {
            var child = new ContentListItem(
                self.content_list,
                self.content_list.url + '/' + entry['id'], entry);
            var childElement = $('<tr />');
            childElement.attr('id', self.content_list.itemDomId(child));
            childElement.addClass(index % 2 ? "even" : "odd");
            var childView = new ContentListItemView(childElement, child);
            childView.render();
            if (self.content_list.isSelected(child))
                childView.disableSelectButton()
            self.element.append(childElement);
        });
};

var Action = function(element, contentListView) {
    var self = this;
    this.element = $(element);
    this.contentListView = contentListView;
    this.run = function(){ }
    this.element.click(function(event){
        event.preventDefault();
        self.run.apply(self, [event]);
    });
};

var Refresh = function(element, contentListView) {
    Action.apply(this, [element, contentListView]);
    this.run = function() {
        contentList = this.contentListView.content_list;
        if (contentList) {
            contentList.populate(contentList.url);
        }
    };
};

var Add = function(element, contentListView) {
    Action.apply(this, [element, contentListView]);
    this.run = function() {
        var contentList = this.contentListView.content_list;
        if (contentList.current) {
            var url = contentList.current.url + '/edit/+'
            window.open(url);
        }
    };
}

ContentListView.prototype.buildActions = function() {
  var refreshLink = $('<a href="#">refresh</a>');
  var refresh = new Refresh(refreshLink, this);
  var addLink = $('<a href="#">add in current folder</a>');
  var add = new Add(addLink, this);

  this.content_list.actionListElement.empty();
  this.content_list.actionListElement.append(refreshLink, addLink);
};

var ContentListSelectionView = function(element, contentList) {
    this.element = $(element);
    this.contentList = contentList;
};

ContentListSelectionView.prototype.appendSelectionItem = function(item) {
    var self = this;
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
        content_list, url, info) {
    this.content_list = content_list;
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
    var self = this;
    this.element.empty();
    var current = (this.item.info['id'] == '.')
    var icon_cell = $('<td class="cell_icon" />');
    var actions_cell = $('<td class="cell_actions" />');
    var id_cell = $('<td class="cell_id" />');
    var icon = $('<img />');
    var title_cell = $('<td class="cell_title" />');
    var link = null

    if (this.item.info['folderish'] && !current) {
        this.element.addClass("folderish");
        id_cell.append($('<a href="#">' + self.item.info['id'] + "</a>"))
        link = $('<a href="#" />');
        this.element.click(function(event){
            self.item.content_list.populate.apply(
                self.item.content_list, [self.item.url]);
            return false;
        });
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
            self.item.content_list._itemClicked.apply(self.item.content_list,
                [event, self.item]);
            event.stopPropagation();
        });
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
    var self = this;
    var icon_cell = $('<td class="cell_icon" />');
    var actions_cell = $('<td class="cell_actions" />');
    var id_cell = $('<td class="cell_id" />');
    var icon = $('<img />');
    var title_cell = $('<td class="cell_title" />');
    var link = $('<span />');;

    var removeButton = $('<img class="button reference_remove"' +
        'src="../++resource++silva.core.references.widgets/delete.png" />');
    removeButton.click(function(event){
        self.item.content_list._itemRemovedFromSelection.apply(
            self.item.content_list, [event, self.item]);
    });
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
    this.reference_interface = $('#' + this.id + '-interface');
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
    var self = this;
    var options = {'intid': intid};

    this.link.text('loading ...');
    if (this.reference_input) {
        this.reference_input.val(intid);
    };
    if (this.reference_interface.val()) {
        options['interface'] = this.reference_interface.val();
    };
    $.getJSON(url + '/++rest++items', options,
              function(data) {
                  self.render.apply(self, [data]);
              });
};

ReferencedRemoteObject.prototype.render = function(info) {
    // Render a link to a remote object from fetched information.
    var self = this;
    var icon = $('<img />');
    var set_or_remove_attr = function(name, value) {
        if (value) {
            self.link.attr(name, value);
        }
        else {
            self.link.removeAttr(name);
        };
    };

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
    'display_field': 'title',
    // link title attribute
    'title_field': 'id',
    // max items to display besides root
    'max_items': 3};
    options = options || {};
    this.options = {};
    $.extend(this.options, default_options, options);
};

PathList.prototype.fetch = function(info) {
    var self = this;
    var url = info['url'];
    $.getJSON(url + '/++rest++parents',
                function(data) {
                    self.render.apply(self, [data]);
                });
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
    var outer = $('<span class="path_outer" />');
    var inner = $('<span class="path_inner" />');
    // var img = $('<img />')
    var link = $('<span class="path_fake" />');
    link.text('...');
    link.appendTo(inner);
    inner.appendTo(outer);
    return outer;
};

PathList.prototype._build_entry = function(info) {
    var self = this;
    var outer = $('<span class="path_outer" />');
    var inner = $('<span class="path_inner" />');
    var link = $('<a href="#" />');
    link.attr('title', info[this.options['title_field']])
    link.text(info[this.options['display_field']]);
    link.data('++rest++', info);

    link.click(function(event){
        var data = $(this).data('++rest++');
        self._notify.apply(self, [event, data]);
        return false;
    });

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
        var content_list = new ContentList(
            popup, widget_id, {'multiple': false});
        content_list.element.bind('content-list-item-selected',
            function(event, item) {
                var reference = new ReferencedRemoteObject(widget_id);
                reference.render(item.info);
                var popup = $('#' + widget_id + '-dialog');
                popup.dialog('close');
            });
        content_list.populate(url);
        popup.dialog('open');
        return false;
    });
});
