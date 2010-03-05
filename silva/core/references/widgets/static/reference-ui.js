var ContentList = function(element, widget_id) {
    this.element = $(element);
    this.widget_id = widget_id;
};

ContentList.prototype.populate = function(url) {
    var self = this;
    $.getJSON(url + '/++rest++items', function (data) {
            self.element.empty();
            $.each(data, function(index, entry) {
                    var child = new ContentListItem(self,
                                                    url + '/' + entry['id'],
                                                    entry['title'],
                                                    entry['type'],
                                                    entry['icon'],
                                                    entry['intid']);
                    child.build(self.element);
                });
        });
};

var ContentListItem = function(content_list, url, title, type, icon, intid) {
    this.content_list = content_list;
    this.url = url;
    this.title = title;
    this.type = type;
    this.icon = icon;
    this.intid = intid;
};

ContentListItem.prototype.build = function(root) {
    var self = this;
    var link = $('<a />');
    var icon = $('<img />');
    var use = $('<input type="checkbox" />');
    var item = $('<li />');

    link.text(self.title);
    link.click(function(event){
            self.content_list.populate.apply(self.content_list, [self.url]);
            return false;
        });
    link.prependTo(item);

    icon.attr('src', self.icon);
    icon.prependTo(item);

    use.click(function(event){
        var content_link = $('#' + self.content_list.widget_id + '-link');
        content_link.text(self.title);
        content_link.attr('href', self.url);
        var content_value = $('#' + self.content_list.widget_id + '-value');
        content_value.attr('value', self.intid);
        var popup = $('#' + self.content_list.widget_id + '-dialog');
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


