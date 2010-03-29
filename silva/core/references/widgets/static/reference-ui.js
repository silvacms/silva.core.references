var ContentList = function(element, widget_id) {
    this.element = $(element);
    this.widget_id = widget_id;
};

ContentList.prototype.populate = function(url) {
    var self = this;
    $.getJSON(url + '/++rest++items', function (data) {
            self.element.empty();
            $.each(data, function(index, entry) {
                    var child = new ContentListItem(
                        self, url + '/' + entry['id'], entry);
                    child.build(self.element);
                });
        });
};

var ReferencedRemoteObject = function(widget_id) {
    // Refer a link that can represent a remote object on the
    // server. Its referenece (intid) can be store in a input called
    // widget_id-value.
    this.id = widget_id;
    this.widget = $('#' + this.id);
    this.link = $('#' + this.id + '-link');
    this.reference_input = $('#' + this.id + '-value');
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

    this.link.text('loading ...');
    if (this.reference_input) {
        this.reference_input.val(intid);
    };
    $.getJSON(url + '/++rest++items', {'intid': intid},
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
}

ReferencedRemoteObject.prototype.hide = function() {
    // Hide widget
    this.widget.hide();
}

ReferencedRemoteObject.prototype.toggle = function() {
    // Hide/display widget
    this.widget.toggle();
}


var ContentListItem = function(
        content_list, url, info) {
    this.content_list = content_list;
    this.url = url;
    this.info = info;
};

ContentListItem.prototype.build = function(root) {
    var self = this;
    var link = $('<a />');
    var icon = $('<img />');
    var use = $('<input type="checkbox" />');
    var item = $('<li />');

    link.text(self.info['title']);
    link.click(function(event){
            self.content_list.populate.apply(self.content_list, [self.url]);
            return false;
        });
    link.prependTo(item);

    icon.attr('src', self.info['icon']);
    icon.prependTo(item);

    use.click(function(event){
        var id = self.content_list.widget_id;
        var popup = $('#' + id  + '-dialog');
        var reference = new ReferencedRemoteObject(id);

        reference.render(self.info);
        popup.dialog('close');
    });
    use.prependTo(item);

    item.appendTo(root);
};

$(document).ready(function() {

   $('.reference-dialog').dialog({
        autoOpen: false,
        modal: true,
        height: 500,
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


