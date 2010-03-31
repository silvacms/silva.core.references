var ContentList = function(element, widget_id) {
    this.id = widget_id;
    this.element = $(element);
    this.reference_interface = $('#' + this.id + '-interface');
    this.parent = null;
    this.current = null;
};

function extract_from_id(data, id) {
    for(var i=0; i < data.length; i++) {
        if (data[i]['id'] == id) {
            return data.splice(i, 1)[0];
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

    $.getJSON(url + '/++rest++items', options, function (data) {
        self.element.empty();
        var root = $('<ul class="content_list" />');
        root.appendTo(self.element);
        // get rid of '.' and '..'
        self.current = extract_from_id(data, '.');
        self.parent = extract_from_id(data, '..');
        self.build_path.apply(self);
        $.each(data, function(index, entry) {
                var child = new ContentListItem(
                    self, url + '/' + entry['id'], entry);
                child.build(root);
        });
    });
};

ContentList.prototype.build_path = function() {
    var self = this;
    var element = this.element.find("div.path_list");
    if (element.length == 0) {
        element = $('<div class="path_list" />');
    }
    var path_list = new PathList(element);
    this.element.prepend(element);
    path_list.fetch(this.current);
    path_list.bind(function(event, data){
        self.populate.apply(self, [data['url']]);
    });
};

var ContentListItem = function(
        content_list, url, info) {
    this.content_list = content_list;
    this.url = url;
    this.info = info;
};

ContentListItem.prototype.build = function(root) {
    var self = this;
    var icon = $('<img />');
    var item = $('<li />');
    var link = null
    if (self.info['folderish']) {
        link = $('<a href="#" />');
        link.click(function(event){
                self.content_list.populate.apply(self.content_list, [self.url]);
                return false;
            });
    } else {
        link = $('<span />');
    }

    link.data('++rest++', self.info);
    link.text(self.info['title']);
    link.prependTo(item);

    icon.attr('src', self.info['icon']);
    icon.prependTo(item);

    if (self.info['implements']) {
        var use = $('<input type="checkbox" />');
        use.click(function(event){
            var id = self.content_list.id;
            var popup = $('#' + id  + '-dialog');
            var reference = new ReferencedRemoteObject(id);

            reference.render(self.info);
            popup.dialog('close');
        });
        use.prependTo(item);
    }

    item.appendTo(root);
};


var ReferencedRemoteObject = function(widget_id) {
    // Refer a link that can represent a remote object on the
    // server. Its referenece (intid) can be store in a input called
    // widget_id-value.
    this.id = widget_id;
    this.widget = $('#' + this.id);
    this.link = $('#' + this.id + '-link');
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
    this.link.text(reason);
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
    var icon = $('<img />');

    this.link.empty();
    this.link.text(info['title']);
    this.link.attr('href', info['url']);
    this.link.attr('title', info['path']);
    this.link.data('content', info);
    icon.attr('src', info['icon']);
    icon.prependTo(this.link);
    if (this.reference_input) {
        this.reference_input.val(info['intid']);
    };
    this.link.trigger('reference-modified', info);
};

ReferencedRemoteObject.prototype.bind = function(callback) {
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

var PathList = function(node, options) {
    this.node = $(node);
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
    this.node.empty();
    this.node.append(this._build_entry(data[0]));

    if (max_items != 0 && len > (max_items + 1)) {
        start = len - max_items;
        this.node.append(this._build_fake());
    }

    for(var i = start; i < stop; i++) {
        this.node.append(this._build_entry(data[i]));
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
    // var img = $('<img />')
    var link = $('<a href="#" />');
    link.attr('title', info[this.options['title_field']])
    link.text(info[this.options['display_field']]);
    link.data('++rest++', info);

    link.click(function(event){
        var data = $(this).data('++rest++');
        self._notify(event, data);
        return false;
    });

    // img.attr('src', info['icon']);
    // link.prepend(img);

    link.appendTo(inner);
    inner.appendTo(outer);
    return outer;
}

PathList.prototype._notify = function(event, data) {
  this.node.trigger('path-modified', data);
}

PathList.prototype.bind = function(callback) {
    this.node.bind('path-modified', callback);
}

$(document).ready(function() {

   $('.reference-dialog').dialog({
        autoOpen: false,
        modal: true,
        height: 500,
        width: 600,
        buttons: {
            'Cancel': function() {
                $(this).dialog('close');
            }
        }
   });

   $('.reference-dialog-trigger').click(function() {
        var widget_id = $(this).parent('.reference-widget').attr('id');
        var popup = $('#' + widget_id + '-dialog');
        var url = $('#' + widget_id + '-base').val();
        var content_list = new ContentList(popup, widget_id);
        content_list.populate(url);
        popup.dialog('open');
        return false;
    });

});


