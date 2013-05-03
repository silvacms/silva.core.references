
(function(infrae, $, jsontemplate) {

    // We use a LazyCallbacks to prevent the browser to freeze on large folders.
    var worker = infrae.deferred.LazyCallbacks();

    var ContentList = function($popup, manager, smi) {
        var listings = $([]),
            self = this;  // To bind events...

        this.$list = $popup.find('.content-list');
        this.$elements = this.$list.find('table.source-list tbody');
        this.options = manager.configuration;
        this.selected = []; // Keep a list of selected items.

        for (var i=0, len=this.options.selected.length; i< len; i++) {
            // Selected needs to be numbers, like they are in the JSON.
            this.selected.push(+this.options.selected[i]);
        };

        listings = listings.add(this.$elements);

        if (this.options.multiple === true) {
            var selection = new SelectionList($popup, manager, smi);
            listings = listings.add(selection.$element);

            // Bind events on multiple management.
            $popup.bind('deselected-smireferences', function(event, item) {
                // A content is unselected
                var view = new ContentListItemView(item, true),
                    index = $.inArray(item.intid, self.selected);
                view.find();
                view.unselect();
                if (index > -1) {
                    self.selected.splice(index, 1);
                };
            });
            $popup.bind('selected-smireferences', function(event, item) {
                // A content is selected
                var view = new ContentListItemView(item, false);
                view.find();
                view.select();
                self.selected.push(item.intid);
            });
        };

        // Bind events on listings.
        // listings.delegate('a.preview-icon', 'click', false);
        listings.delegate('tr.folderish', 'mouseenter', function(event){
            $(this).addClass('folderish-hover');
        });
        listings.delegate('tr.folderish', 'mouseleave', function(event){
            $(this).removeClass('folderish-hover');
        });
        this.$elements.delegate('tr.folderish', 'click', function(event) {
            // If you click a folderish line, we open it.
            manager.open($(this).data('smilisting').url);
            return false;
        });
        this.$elements.delegate('img.reference-add', 'click', function(event) {
            // If you click on add, add the element to the selection.
            var $item = $(this).closest('tr.item');
            $item.trigger('selected-smireferences', [$item.data('smilisting')]);
            event.stopPropagation();
            return false;
        });
    };

    ContentList.prototype.open = function(url) {
        var self = this,
            options = {
            url: url + '/++rest++silva.core.references.items',
            data: {}};

        if (self.options.iface) {
            options.data['interface'] = self.options.iface;
        };
        if (self.options.show_index) {
            options.data['show_index'] = 'true';
        };

        self.$elements.empty();
        return $.ajax(options).then(function(data) {
            self.render(data);
            return {
                $content: self.$list,
                insert: function($current) {
                    return this.$content;
                }
            };
        });
    };

    ContentList.prototype.render = function(items) {
        var self = this;

        worker.reset();
        self.$elements.empty();
        worker.add(items, function(item) {
            var view = new ContentListItemView(item, self.used(item));
            self.$elements.append(view.render());
        });
    };

    ContentList.prototype.used = function(item) {
        // Return true if the item is selected.
        return $.inArray(item.intid, this.selected) > -1;
    };

    // Render a list item
    var ContentListItemView = function(item, selected) {
        this.item = item;
        this.$item = $([]);
        this.id = item.id;
        if (item.id == '.') {
            this.id = 'current container';
        }
        this.htmlid = 'content-item-' + item['intid'];
        this.selected = selected;
        this.selectable = this.item['implements'] && selected !== true;
    };

    ContentListItemView.prototype.find = function() {
        this.$item = $('#' + this.htmlid);
    };

    ContentListItemView.prototype.select = function() {
        if (this.$item.length && this.selectable) {
            this.$item.find('td.actions').empty();
            this.$item.addClass('selected');
            this.selectable = false;
            this.selected = false;
        };
    };

    ContentListItemView.prototype.unselect = function() {
        if (this.$item.length &&!this.selectable) {
            this.$item.find('td.actions').html(
                '<img class="button reference-add" src="++static++/silva.core.references.widgets/add.png" />');
            this.$item.removeClass('selected');
            this.selectable = true;
            this.selected = true;
        };
    };

    var ContentListItemTemplate = new jsontemplate.Template('<tr class="{classes|html-attr-value}" id="{htmlid|html-attr-value}"><td><a class="preview-icon"><ins class="icon"></ins></a></td><td class="item-id">{id|html}</td><td class="item-title">{item.title|html}</td><td class="actions">{.section selectable}<img class="button reference-add" src="++static++/silva.core.references.widgets/add.png" />{.end}</td></tr>');

    ContentListItemView.prototype.render = function() {
        var classes = ['item'],
            $item;

        if (this.item.id == '.') {
            classes.push('top');
        } else if (this.item.folderish) {
            classes.push("folderish");
        };
        if (this.selected) {
            classes.push('selected');
        };
        this.classes = classes.join(' ');
        $item = $(ContentListItemTemplate.expand(this));
        $item.data('smilisting', this.item);
        infrae.ui.icon($item.find('ins.icon'), this.item.icon);
        this.$item = $item;
        return $item;
    };

    // End of render a list item

    var SelectionList = function($popup, manager, smi) {
        this.$list = $popup.find('table.selection-list');
        this.$elements = this.$list.find('tbody');
        this.options = manager.configuration;

        var self = this;
        // Load already select items
        if (this.options.selected.length > 0) {
            $.each(this.options.selected, function(index, identifier) {
                var url = '++rest++silva.core.references.items';
                $.getJSON(url, {intid: identifier}, function(entry) {
                    self.add(entry);
                });
            });
        };

        // Bind events.
        this.$elements.delegate('img.reference-remove', 'click', function(event) {
            var $item = $(this).closest('tr.item');
            $item.trigger('deselected-smireferences', [$item.data('smilisting')]);
            event.stopPropagation();
            return false;
        });
        $popup.bind('deselected-smireferences', function(event, item) {
            // A content is unselected.
            var view = new SelectionListItemView(item);
            view.find();
            view.remove();
        });
        $popup.bind('selected-smireferences', function(event, item) {
            // A content is selected.
            self.add(item);
        });
        this.$list.show();
    };

    SelectionList.prototype.add = function(item) {
        var view = new SelectionListItemView(item);
        this.$elements.append(view.render());
    };

    var SelectionListItemView = function(item) {
        this.item = item;
        this.htmlid = 'selection-item-' + item['intid'];
        this.$item = undefined;
    };

    SelectionListItemView.prototype.find = function(item) {
        this.$item = $('#' + this.htmlid);
    };

    SelectionListItemView.prototype.remove = function() {
        if (this.$item !== undefined) {
            this.$item.remove();
        };
    };

    var SelectionListItemTemplate = new jsontemplate.Template('<tr class="item" id="{htmlid|html-attr-value}"><td><a class="preview-icon"><ins class="icon"></ins></a></td><td class="item-id">{item.path|html}</td><td class="item-title">{item.title|html}</td><td class="actions"><img class="button reference-remove" src="++static++/silva.core.references.widgets/delete.png" /></td></tr>');

    SelectionListItemView.prototype.render = function() {
        var $item = $(SelectionListItemTemplate.expand(this));
        infrae.ui.icon($item.find('ins.icon'), this.item.icon);
        $item.data('smilisting', this.item);
        this.$item = $item;
        return $item;
    };

    $.extend(infrae.smi.reference, {
        Listing: ContentList
    });

})(infrae, jQuery, jsontemplate);
