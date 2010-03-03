var ContentList = function(element) {
    this.element = $(element);
};

ContentList.prototype.populate = function(url) {
    var self = this;
    $.getJSON(url + '/++rest++items', function (data) {
            self.element.empty();
            $.each(data, function(index, entry) {
                    var child = new ContentListItem(self,
                                                    url + '/' + entry['id'],
                                                    entry['title'],
                                                    entry['type']);
                    child.build(self.element);
                });
        });
};

var ContentListItem = function(content_list, url, title, type) {
    this.content_list = content_list;
    this.url = url;
    this.title = title;
    this.type = type;
};

ContentListItem.prototype.build = function(root) {
    var self = this;
    var item = $('<li />');
    item.text(self.title);
    item.click(function(event){
            self.content_list.populate.apply(self.content_list, [self.url]);
        });
    item.appendTo(root);
};

$(document).ready(function() {

   $('.reference-dialog').dialog({
        autoOpen: false,
            modal: true,
            buttons: {
            'Cancel': function() {
                $(this).dialog('close');
            }
        },
   });

   $('.reference-dialog-trigger').click(function() {
        var url = 'http://localhost:8080/silva/docs';
        var widget = $(this).parent('.reference-widget');
        var popup = $('#' + widget.attr('id') + '-dialog');
        var content_list = new ContentList(popup);
        content_list.populate(url);
        popup.dialog('open');
        return false;
    });

});


