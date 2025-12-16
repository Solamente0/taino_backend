// static/admin/js/banner_admin.js

(function ($) {
    'use strict';

    $(document).ready(function () {
        // نمایش/مخفی کردن فیلدها بر اساس نوع بنر
        const bannerTypeField = $('#id_banner_type');
        const fileField = $('.field-file');
        const iframeCodeField = $('.field-iframe_code');
        const iframeHeightField = $('.field-iframe_height');
        const textFields = $('.field-header_text, .field-bold_text, .field-footer_text');
        const linkFields = $('.field-link_title, .field-link');

        function toggleFields() {
            const bannerType = bannerTypeField.val();

            if (bannerType === 'image') {
                // نمایش فیلدهای مربوط به تصویر
                fileField.show();
                textFields.show();
                linkFields.show();

                // مخفی کردن فیلدهای iframe
                iframeCodeField.hide();
                iframeHeightField.hide();

                // اضافه کردن required به file
                $('#id_file').attr('required', 'required');
                $('#id_iframe_code').removeAttr('required');
            } else if (bannerType === 'iframe' || bannerType === 'embed') {
                // نمایش فیلدهای iframe
                iframeCodeField.show();
                iframeHeightField.show();

                // مخفی کردن فیلدهای تصویر
                fileField.hide();
                textFields.hide();
                linkFields.hide();

                // اضافه کردن required به iframe_code
                $('#id_iframe_code').attr('required', 'required');
                $('#id_file').removeAttr('required');
            }
        }

        // اجرای تابع در بارگذاری صفحه
        if (bannerTypeField.length) {
            toggleFields();

            // اجرای تابع در تغییر نوع بنر
            bannerTypeField.change(toggleFields);
        }

        // پیش‌نمایش زنده تصویر
        const fileInput = $('#id_file');
        if (fileInput.length) {
            fileInput.change(function () {
                const selectedOption = $(this).find('option:selected');
                if (selectedOption.val()) {
                    // شما می‌توانید اینجا لاجیک پیش‌نمایش تصویر را اضافه کنید
                    console.log('File selected:', selectedOption.text());
                }
            });
        }

        // اعتبارسنجی کد iframe/embed
        const iframeCodeInput = $('#id_iframe_code');
        if (iframeCodeInput.length) {
            iframeCodeInput.on('blur', function () {
                const code = $(this).val().trim();
                const bannerType = bannerTypeField.val();

                if (code && (bannerType === 'iframe' || bannerType === 'embed')) {
                    // چک کردن وجود تگ iframe یا script
                    if (bannerType === 'iframe' && !code.includes('<iframe')) {
                        alert('⚠️ کد وارد شده باید شامل تگ <iframe> باشد.');
                    }
                }
            });
        }

        // نمایش تعداد کاراکترها برای فیلدهای متنی
        function addCharacterCounter(fieldId, maxLength) {
            const field = $(fieldId);
            if (field.length) {
                const counter = $('<div class="character-counter" style="font-size: 11px; color: #666; margin-top: 3px;"></div>');
                field.after(counter);

                function updateCounter() {
                    const length = field.val().length;
                    const remaining = maxLength - length;
                    counter.text(`${length} / ${maxLength} کاراکتر`);

                    if (remaining < 0) {
                        counter.css('color', '#dc2626');
                    } else if (remaining < 20) {
                        counter.css('color', '#f59e0b');
                    } else {
                        counter.css('color', '#666');
                    }
                }

                updateCounter();
                field.on('input', updateCounter);
            }
        }

        // اضافه کردن شمارنده برای فیلدهای متنی
        addCharacterCounter('#id_header_text', 255);
        addCharacterCounter('#id_bold_text', 255);
        addCharacterCounter('#id_footer_text', 255);
        addCharacterCounter('#id_link_title', 255);
        addCharacterCounter('#id_link', 1000);

        // رنگ‌آمیزی فیلد where_to_place
        const wherePlaceField = $('#id_where_to_place');
        if (wherePlaceField.length) {
            wherePlaceField.on('blur', function () {
                const value = $(this).val().trim();
                if (value === 'root') {
                    $(this).css({
                        'background-color': '#fef3c7',
                        'border-color': '#f59e0b'
                    });
                } else if (value.startsWith('/dashboard')) {
                    $(this).css({
                        'background-color': '#dbeafe',
                        'border-color': '#3b82f6'
                    });
                } else {
                    $(this).css({
                        'background-color': 'white',
                        'border-color': '#ccc'
                    });
                }
            });

            // اجرای یکبار در بارگذاری
            wherePlaceField.trigger('blur');
        }

        // اضافه کردن دکمه کپی برای iframe_code
        if (iframeCodeInput.length) {
            const copyButton = $('<button type="button" class="button" style="margin-top: 5px;">📋 کپی کد</button>');
            copyButton.on('click', function (e) {
                e.preventDefault();
                const code = iframeCodeInput.val();

                // کپی به کلیپبورد
                navigator.clipboard.writeText(code).then(function () {
                    copyButton.text('✓ کپی شد!');
                    setTimeout(function () {
                        copyButton.text('📋 کپی کد');
                    }, 2000);
                }).catch(function (err) {
                    alert('خطا در کپی کردن: ' + err);
                });
            });

            iframeCodeInput.after(copyButton);
        }

        // هشدار برای تغییر where_to_place
        const originalWherePlaceValue = wherePlaceField.val();
        wherePlaceField.on('change', function () {
            const newValue = $(this).val();
            if (originalWherePlaceValue && newValue !== originalWherePlaceValue) {
                if (!confirm('⚠️ تغییر محل نمایش بنر ممکن است باعث شود بنر در صفحه فعلی نمایش داده نشود. آیا مطمئن هستید؟')) {
                    $(this).val(originalWherePlaceValue);
                }
            }
        });

        // نمایش پیام راهنما برای where_to_place
        if (wherePlaceField.length) {
            const helpText = $('<div class="help" style="margin-top: 5px; font-size: 12px; color: #666;"></div>');
            helpText.html(`
                <strong>راهنما:</strong><br>
                • برای صفحه اصلی: <code>root</code><br>
                • برای صفحات دیگر: <code>/dashboard/path</code><br>
                • مثال: <code>/dashboard/lawyer/cases</code>
            `);
            wherePlaceField.after(helpText);
        }

        // کمک برای فیلد display_duration
        const durationField = $('#id_display_duration');
        if (durationField.length) {
            // اضافه کردن helper text
            const durationHelper = $('<div class="duration-helper"></div>');
            durationHelper.html(`
                <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 10px; border-radius: 4px; margin-top: 8px; font-size: 12px;">
                    <strong>💡 راهنما:</strong><br>
                    • 1 ثانیه = 1000 میلی‌ثانیه<br>
                    • 3 ثانیه = 3000 میلی‌ثانیه<br>
                    • 5 ثانیه = 5000 میلی‌ثانیه (پیش‌فرض)<br>
                    • 10 ثانیه = 10000 میلی‌ثانیه
                </div>
                <div class="duration-display" style="margin-top: 8px; font-size: 13px; color: #1e40af; font-weight: 600;"></div>
            `);
            durationField.after(durationHelper);

            // نمایش زنده تبدیل به ثانیه
            function updateDurationDisplay() {
                const ms = parseInt(durationField.val()) || 5000;
                const seconds = (ms / 1000).toFixed(1);
                $('.duration-display').html(`
                    ⏱️ <strong>${ms}</strong> میلی‌ثانیه = <strong>${seconds}</strong> ثانیه
                `);
            }

            updateDurationDisplay();
            durationField.on('input change', updateDurationDisplay);

            // دکمه‌های سریع
            const quickButtons = $(`
                <div style="margin-top: 8px; display: flex; gap: 5px; flex-wrap: wrap;">
                    <button type="button" class="button small" data-duration="3000">3 ثانیه</button>
                    <button type="button" class="button small" data-duration="5000">5 ثانیه</button>
                    <button type="button" class="button small" data-duration="7000">7 ثانیه</button>
                    <button type="button" class="button small" data-duration="10000">10 ثانیه</button>
                    <button type="button" class="button small" data-duration="15000">15 ثانیه</button>
                </div>
            `);

            quickButtons.find('button').on('click', function (e) {
                e.preventDefault();
                const duration = $(this).data('duration');
                durationField.val(duration);
                updateDurationDisplay();
            });

            durationHelper.append(quickButtons);
        }

        // نمایش پیام راهنما برای where_to_place
        if ($('.change-list').length) {
            console.log('✓ Banner Admin JavaScript loaded successfully');
        }
    });
})(django.jQuery);
