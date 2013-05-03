
(function(infrae, $, jsontemplate) {

    $.extend(infrae.smi.reference, {
        Adder: function($popup, manager, smi, addable) {
            var $content = $('<div class="content-list" />');
            var $form = null;
            var form_url = null;
            var action = null;

        return {
            open: function(url) {
                form_url = url + '/++rest++silva.core.references.adding/' + addable;

                var render = function(data) {
                    $content.html(data.screen.forms);
                    $form = $content.children('form');
                    $form.attr('data-form-url', form_url);

                    if (action !== null) {
                        // The form changed, just rebind and reinitialize it.
                        $form.bind('submit', action);
                        $form.trigger('load-smiform', {form: $form, container: $form});
                        return {};
                    }

                    // First render, return the new content and the new actions
                    action = function() {
                        var values = $form.serializeArray();
                        // XXX Save action is kind of hardcoded ..
                        values.push({
                            name: $form.attr('name') + '.action.save',
                            value: 'Save'});
                        smi.ajax.query(form_url, values).then(function (data) {
                            // The add form redirect on success.
                            if (infrae.interfaces.is_implemented_by('redirect', data)) {
                                manager.back();
                            } else {
                                render(data);
                            };
                        });
                        return false;
                    };
                    $form.bind('submit', action);

                    return {
                        insert: function($current) {
                            // The form is inserted.
                            if ($content !== $current) {
                                $content.hide();
                                $content.insertAfter($current);
                                $current.slideUp();
                                $content.slideDown();
                            };
                            $form.trigger('load-smiform', {form: $form, container: $form});
                            return $content;
                        },
                        $content: $content,
                        actions: {
                            Back: manager.back,
                            Add: action
                        }
                    };
                };

                return smi.ajax.query(form_url).then(render);
            },
            update: function(new_addable) {
                addable = new_addable;
            }
        };
            }
   });

})(infrae, jQuery, jsontemplate);
