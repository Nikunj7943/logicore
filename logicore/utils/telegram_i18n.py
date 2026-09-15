"""
utils/telegram_i18n.py
Bilingual (English / Hindi) message strings for the Telegram bot.

Usage:
    from logicore.utils.telegram_i18n import t, get_lang

    t("greeting", lang, name="Ramesh")
"""

import frappe

DEFAULT_LANG = "en"

TEXT = {
    "lang_select": {
        "en": "🌐 Please select your language:\nअपनी भाषा चुनें:",
        "hi": "🌐 Please select your language:\nअपनी भाषा चुनें:",
    },
    "language_set": {
        "en": "✅ Language set to English.",
        "hi": "✅ भाषा हिन्दी में सेट कर दी गई है।",
    },
    "language_changed_continue": {
        "en": "✅ Language changed to English. Continue where you left off 👇",
        "hi": "✅ भाषा हिन्दी में बदल दी गई। जहाँ छोड़ा था वहीं से जारी रखें 👇",
    },
    "account_deactivated": {
        "en": "⛔ Your account is deactivated. Contact admin.",
        "hi": "⛔ आपका अकाउंट निष्क्रिय कर दिया गया है। एडमिन से संपर्क करें।",
    },
    "album_warning": {
        "en": "⚠️ Please send photos <b>one at a time</b>, not as a group.\n\n"
              "Send the first photo, wait for the ✅ confirmation, then send the next one.",
        "hi": "⚠️ कृपया फोटो <b>एक-एक करके</b> भेजें, ग्रुप (एल्बम) में नहीं।\n\n"
              "पहली फोटो भेजें, ✅ कन्फर्मेशन का इंतज़ार करें, फिर अगली भेजें।",
    },
    "cancel_before_photo": {
        "en": "Please /cancel the current task before uploading a POD photo.",
        "hi": "POD फोटो अपलोड करने से पहले कृपया /cancel करें।",
    },
    "choose_first": {
        "en": "📎 Please choose what to do first 👇",
        "hi": "📎 कृपया पहले बताएं कि क्या करना है 👇",
    },
    "linked_trip_saving": {
        "en": "✅ Linked to Trip <b>{trip}</b>.\n⏳ Saving pending photos…",
        "hi": "✅ Trip <b>{trip}</b> से लिंक हो गया।\n⏳ फोटो सेव हो रही हैं…",
    },
    "linked_trip_send_images": {
        "en": "✅ Linked to Trip <b>{trip}</b>.\nSend the POD photos now.",
        "hi": "✅ Trip <b>{trip}</b> से लिंक हो गया।\nअब POD फोटो भेजें।",
    },
    "trip_not_found": {
        "en": "⚠️ Trip <code>{trip}</code> not found.\nCheck the number and resend, or /cancel.",
        "hi": "⚠️ Trip <code>{trip}</code> नहीं मिला।\nनंबर चेक करके फिर भेजें, या /cancel करें।",
    },
    "keep_sending_images": {
        "en": "📷 Keep sending photos.\nType /done to upload what you have, or /cancel.",
        "hi": "📷 फोटो भेजते रहें।\nअपलोड करने के लिए /done टाइप करें, या /cancel करें।",
    },
    "nothing_to_finish": {
        "en": "Nothing to finish. Use /menu to start.",
        "hi": "कुछ भी पूरा करने को नहीं है। शुरू करने के लिए /menu टाइप करें।",
    },
    "cancelled_returning": {
        "en": "❌ Cancelled. Returning to menu.",
        "hi": "❌ रद्द किया गया। मेनू पर लौट रहे हैं।",
    },
    "unknown_command": {
        "en": "Unknown command. Type /menu for options.",
        "hi": "अनजान कमांड। विकल्पों के लिए /menu टाइप करें।",
    },
    "download_photo_failed": {
        "en": "⚠️ Could not download photo. Try again.",
        "hi": "⚠️ फोटो डाउनलोड नहीं हो पाई। फिर से कोशिश करें।",
    },
    "image_replaced": {
        "en": "🔄 Photo {seq} replaced!\nTrip: <b>{trip}</b>",
        "hi": "🔄 फोटो {seq} बदल दी गई!\nTrip: <b>{trip}</b>",
    },
    "multiple_trips_prompt": {
        "en": "You have multiple trips in progress. Which trip is this photo for?",
        "hi": "आपके कई Trip प्रोसेस में हैं। यह फोटो किस Trip के लिए है?",
    },
    "photo_saved_no_qr": {
        "en": "📷 Photo saved. QR not detected.\n\n"
              "Reply with the <b>Trip No</b> to link it, or /cancel.",
        "hi": "📷 फोटो सेव हो गई। QR नहीं मिला।\n\n"
              "लिंक करने के लिए <b>Trip No</b> भेजें, या /cancel करें।",
    },
    "new_qr_switched_prefix": {
        "en": "🔀 New QR detected — switched to Trip <b>{trip}</b>.\n\n",
        "hi": "🔀 नया QR मिला — Trip <b>{trip}</b> पर स्विच किया गया।\n\n",
    },
    "image_saved_progress": {
        "en": "📎 Photo <b>{count}</b> uploaded\nTrip: <b>{trip}</b>\n"
              "Send more photos or tap <b>Complete POD</b> when done.",
        "hi": "📎 फोटो <b>{count}</b> अपलोड हो गई\nTrip: <b>{trip}</b>\n"
              "और फोटो भेजें या पूरा होने पर <b>Complete POD</b> दबाएं।",
    },
    "trip_not_identified": {
        "en": "⚠️ Trip not identified yet. Send a photo with QR or type the Trip No.",
        "hi": "⚠️ Trip अभी पहचाना नहीं गया। QR वाली फोटो भेजें या Trip No टाइप करें।",
    },
    "no_active_collection": {
        "en": "⚠️ No active photo collection found. Please resend photos.",
        "hi": "⚠️ कोई एक्टिव फोटो कलेक्शन नहीं मिला। कृपया फोटो फिर से भेजें।",
    },
    "no_images_yet": {
        "en": "⚠️ No photos uploaded yet.",
        "hi": "⚠️ अभी तक कोई फोटो नहीं है।",
    },
    "generating_pod_pdf": {
        "en": "⏳ Generating POD PDF with {count} photo(s) for Trip <b>{trip}</b>…\n"
              "I'll notify you when done.",
        "hi": "⏳ Trip <b>{trip}</b> के लिए {count} फोटो से POD PDF बन रही है…\n"
              "पूरा होने पर बताया जाएगा।",
    },
    "pdf_or_photo_required": {
        "en": "⚠️ Please send a <b>PDF</b> or photo of the POD.",
        "hi": "⚠️ कृपया POD की <b>PDF</b> या फोटो भेजें।",
    },
    "pdf_cannot_mix_photos": {
        "en": "⚠️ You're adding <b>photos</b> for Trip <b>{trip}</b> ({count} so far).\n\n"
              "A PDF is a complete POD on its own and can't be mixed with photos.\n\n"
              "• Tap <b>Complete POD</b> (or type /done) to finish these photos first, "
              "then send the PDF separately, or\n"
              "• Type /cancel, then send the PDF.",
        "hi": "⚠️ आप Trip <b>{trip}</b> के लिए <b>फोटो</b> जोड़ रहे हैं (अब तक {count})।\n\n"
              "PDF खुद में पूरी POD होती है, इसे फोटो के साथ नहीं मिला सकते।\n\n"
              "• पहले इन फोटो को पूरा करने के लिए <b>Complete POD</b> दबाएं (या /done टाइप करें), "
              "फिर PDF अलग से भेजें, या\n"
              "• /cancel टाइप करें, फिर PDF भेजें।",
    },
    "processing_pod_pdf": {
        "en": "📄 Processing POD PDF… please wait.",
        "hi": "📄 POD PDF प्रोसेस हो रही है… कृपया प्रतीक्षा करें।",
    },
    "ops_staff_only_create": {
        "en": "⛔ Only Ops Staff can create trips.",
        "hi": "⛔ केवल Ops Staff ही Trip बना सकते हैं।",
    },
    "pdf_tcn_required": {
        "en": "⚠️ Please send a <b>PDF</b> of the TCN Summary Sheet.",
        "hi": "⚠️ कृपया TCN Summary Sheet की <b>PDF</b> भेजें।",
    },
    "pdf_received_extracting": {
        "en": "📄 PDF received. Extracting data… please wait.",
        "hi": "📄 PDF मिल गई। डेटा निकाला जा रहा है… कृपया प्रतीक्षा करें।",
    },
    "not_authorised": {
        "en": "⛔ Not authorised",
        "hi": "⛔ अनुमति नहीं है",
    },
    "processing_short": {
        "en": "Processing…",
        "hi": "प्रोसेस हो रहा है…",
    },
    "replacing_pod_cb": {
        "en": "Replacing POD…",
        "hi": "POD बदली जा रही है…",
    },
    "replacing_pod_progress": {
        "en": "⏳ Replacing POD for Trip <b>{trip}</b>…",
        "hi": "⏳ Trip <b>{trip}</b> की POD बदली जा रही है…",
    },
    "uploading_duplicate_cb": {
        "en": "Uploading duplicate…",
        "hi": "डुप्लिकेट अपलोड हो रहा है…",
    },
    "uploading_duplicate_progress": {
        "en": "⏳ Uploading duplicate POD for Trip <b>{trip}</b>…",
        "hi": "⏳ Trip <b>{trip}</b> के लिए डुप्लिकेट POD अपलोड हो रही है…",
    },
    "send_next_photos": {
        "en": "📷 Send the next photo(s) for Trip <b>{trip}</b>.\nType /cancel to abort.",
        "hi": "📷 Trip <b>{trip}</b> के लिए अगली फोटो भेजें।\nरद्द करने के लिए /cancel टाइप करें।",
    },
    "session_expired_resend_photo": {
        "en": "⚠️ Session expired, resend the photo",
        "hi": "⚠️ सेशन समाप्त हो गया, फोटो फिर से भेजें",
    },
    "could_not_download_photo_resend": {
        "en": "⚠️ Could not download photo. Resend it.",
        "hi": "⚠️ फोटो डाउनलोड नहीं हो पाई। फिर से भेजें।",
    },
    "send_photo_for_image_cb": {
        "en": "Send Photo {seq}",
        "hi": "Photo {seq} भेजें",
    },
    "send_photo_for_image_progress": {
        "en": "📸 Send <b>Photo {seq}</b>.\nType /cancel to abort.",
        "hi": "📸 <b>Photo {seq}</b> भेजें।\nरद्द करने के लिए /cancel टाइप करें।",
    },
    "exited_cb": {
        "en": "Exited",
        "hi": "बाहर निकल गए",
    },
    "exited_upload_progress": {
        "en": "🚪 Exited photo upload. Your progress is saved — send /start to resume anytime.",
        "hi": "🚪 फोटो अपलोड से बाहर निकले। आपकी प्रगति सेव है — कभी भी जारी रखने के लिए /start भेजें।",
    },
    "send_new_photo_for_image_cb": {
        "en": "Send new Photo {seq}",
        "hi": "नई Photo {seq} भेजें",
    },
    "send_replacement_photo_progress": {
        "en": "📸 Send the <b>replacement photo</b> for <b>Photo {seq}</b>.\nType /cancel to abort.",
        "hi": "📸 <b>Photo {seq}</b> के लिए <b>नई फोटो</b> भेजें।\nरद्द करने के लिए /cancel टाइप करें।",
    },
    "creating_trip_cb": {
        "en": "Creating Trip…",
        "hi": "Trip बनाया जा रहा है…",
    },
    "cancelled_cb": {
        "en": "Cancelled",
        "hi": "रद्द किया गया",
    },
    "trip_creation_cancelled": {
        "en": "❌ Trip creation cancelled.",
        "hi": "❌ Trip बनाना रद्द किया गया।",
    },
    "upload_pod_menu_text": {
        "en": "📦 <b>Upload POD</b>\n\n"
              "Send clear <b>photos</b> of the POD pages, or a <b>PDF</b>.\n"
              "Make sure the QR code is fully visible and in focus.\n\n"
              "• <b>Photos</b>: keep sending, then type /done to upload.\n"
              "• <b>PDF</b>: uploads directly.\n\n"
              "Type /cancel to abort.",
        "hi": "📦 <b>Upload POD</b>\n\n"
              "POD पेज की साफ <b>फोटो</b> भेजें, या <b>PDF</b> भेजें।\n"
              "ध्यान रखें कि QR कोड पूरी तरह दिख रहा हो और फोकस में हो।\n\n"
              "• <b>फोटो</b>: भेजते रहें, फिर अपलोड के लिए /done टाइप करें।\n"
              "• <b>PDF</b>: सीधे अपलोड हो जाती है।\n\n"
              "रद्द करने के लिए /cancel टाइप करें।",
    },
    "finish_existing_trip_suffix": {
        "en": "\n\n<b>Or finish an existing trip's POD without new photos:</b>",
        "hi": "\n\n<b>या नई फोटो के बिना किसी मौजूदा Trip की POD पूरी करें:</b>",
    },
    "ops_staff_only_alert": {
        "en": "⛔ Ops Staff only",
        "hi": "⛔ केवल Ops Staff",
    },
    "create_trip_menu_text": {
        "en": "📄 <b>Create Trip</b>\n\n"
              "Send the <b>TCN Summary Sheet PDF</b> as a document "
              "(use the file / attachment icon, not the photo option).\n\n"
              "Type /cancel to abort.",
        "hi": "📄 <b>Create Trip</b>\n\n"
              "<b>TCN Summary Sheet PDF</b> को डॉक्यूमेंट के रूप में भेजें "
              "(फाइल/अटैचमेंट आइकन से, फोटो ऑप्शन से नहीं)।\n\n"
              "रद्द करने के लिए /cancel टाइप करें।",
    },
    "goodbye_cb": {
        "en": "Goodbye 👋",
        "hi": "अलविदा 👋",
    },
    "session_ended": {
        "en": "👋 Session ended. Send /start anytime to begin again.",
        "hi": "👋 सेशन समाप्त हुआ। फिर से शुरू करने के लिए कभी भी /start भेजें।",
    },
    "session_expired_resend_pdf": {
        "en": "⚠️ Session expired. Resend PDF.",
        "hi": "⚠️ सेशन समाप्त हो गया। PDF फिर से भेजें।",
    },
    "trip_created_success": {
        "en": "✅ Trip <b>{trip}</b> created as <i>Draft</i>.\n"
              "Type: <b>{type}</b>\nTCN: <code>{tcn}</code>\n\n"
              "⚠️ Open TMS Desk to fill <b>branch, customer</b> and submit.",
        "hi": "✅ Trip <b>{trip}</b> <i>Draft</i> के रूप में बना दिया गया।\n"
              "Type: <b>{type}</b>\nTCN: <code>{tcn}</code>\n\n"
              "⚠️ <b>branch, customer</b> भरने और सबमिट करने के लिए TMS Desk खोलें।",
    },
    "trip_creation_error": {
        "en": "❌ Error: {error}\nCheck logs.",
        "hi": "❌ त्रुटि: {error}\nलॉग्स देखें।",
    },
    "greeting": {
        "en": "👋 Hi <b>{name}</b>!\n\nWhat would you like to do?",
        "hi": "👋 नमस्ते <b>{name}</b>!\n\nआप क्या करना चाहेंगे?",
    },
    "btn_upload_pod": {
        "en": "📦 Upload POD",
        "hi": "📦 POD अपलोड करें",
    },
    "btn_create_trip": {
        "en": "📄 Create Trip",
        "hi": "📄 Trip बनाएं",
    },
    "btn_exit": {
        "en": "🚪 Exit",
        "hi": "🚪 बाहर जाएं",
    },
    "welcome_share_phone": {
        "en": "👋 <b>Welcome to LogiCore Bot</b>\n\n"
              "Tap the button below to verify your identity 👇",
        "hi": "👋 <b>LogiCore Bot में आपका स्वागत है</b>\n\n"
              "अपनी पहचान वेरीफाई करने के लिए नीचे बटन दबाएं 👇",
    },
    "btn_share_phone": {
        "en": "📱 Share My Phone Number",
        "hi": "📱 अपना फोन नंबर शेयर करें",
    },
    "share_own_number_only": {
        "en": "⚠️ Please share <b>your own</b> phone number only.",
        "hi": "⚠️ कृपया केवल <b>अपना ही</b> फोन नंबर शेयर करें।",
    },
    "welcome_back": {
        "en": "✅ Welcome back, <b>{name}</b>!",
        "hi": "✅ वापसी पर स्वागत है, <b>{name}</b>!",
    },
    "access_denied": {
        "en": "⛔ <b>Access Denied</b>\n\n"
              "Number <code>{phone}</code> is not registered in TMS.\n\n"
              "Contact your TMS admin.",
        "hi": "⛔ <b>एक्सेस नहीं है</b>\n\n"
              "नंबर <code>{phone}</code> TMS में रजिस्टर्ड नहीं है।\n\n"
              "अपने TMS एडमिन से संपर्क करें।",
    },
    "registration_error": {
        "en": "❌ Registration error. Try again.",
        "hi": "❌ रजिस्ट्रेशन में त्रुटि। फिर से कोशिश करें।",
    },
    "registration_failed": {
        "en": "❌ Registration failed. Contact admin.",
        "hi": "❌ रजिस्ट्रेशन असफल। एडमिन से संपर्क करें।",
    },
    "verified_welcome": {
        "en": "✅ <b>Verified!</b>\n\nWelcome, <b>{name}</b>!\nRole: <b>{role}</b>",
        "hi": "✅ <b>वेरीफाई हो गया!</b>\n\nस्वागत है, <b>{name}</b>!\nRole: <b>{role}</b>",
    },

    # ── telegram_tasks.py ────────────────────────────────────────────────────
    "download_files_failed": {
        "en": "⚠️ Could not download your files. Please try again.",
        "hi": "⚠️ आपकी फाइलें डाउनलोड नहीं हो पाईं। फिर से कोशिश करें।",
    },
    "pod_dates_required_blocked": {
        "en": "⚠️ <b>POD Upload Not Allowed</b>\n\nTrip: <b>{trip}</b>\n\n"
              "POD cannot be uploaded until <b>Arrival Date/Time</b> and "
              "<b>Release Date/Time</b> at the Unloading Site have been filled on the Trip.\n\n"
              "Please ask ops to fill these on the Trip, then try again.",
        "hi": "⚠️ <b>POD अपलोड की अनुमति नहीं</b>\n\nTrip: <b>{trip}</b>\n\n"
              "जब तक Trip में Unloading Site का <b>Arrival Date/Time</b> और "
              "<b>Release Date/Time</b> नहीं भरा जाता, POD अपलोड नहीं हो सकती।\n\n"
              "कृपया ops से ये फील्ड भरने के लिए कहें, फिर फिर से कोशिश करें।",
    },
    "pod_dates_required_with_images": {
        "en": "⚠️ <b>POD Upload Not Allowed</b>\n\nTrip: <b>{trip}</b>\n\n"
              "POD cannot be uploaded until <b>Arrival Date/Time</b> and "
              "<b>Release Date/Time</b> at the Unloading Site have been filled.\n\n"
              "Your photos are saved. Once ops fills these fields on the Trip, "
              "tap <b>Complete POD</b> below again — no need to resend photos.",
        "hi": "⚠️ <b>POD अपलोड की अनुमति नहीं</b>\n\nTrip: <b>{trip}</b>\n\n"
              "जब तक Unloading Site का <b>Arrival Date/Time</b> और "
              "<b>Release Date/Time</b> नहीं भरा जाता, POD अपलोड नहीं हो सकती।\n\n"
              "आपकी फोटो सेव हैं। ops द्वारा ये फील्ड भरने के बाद नीचे "
              "<b>Complete POD</b> दबाएं — फोटो फिर से भेजने की ज़रूरत नहीं है।",
    },
    "pod_upload_success_files": {
        "en": "✅ <b>POD Uploaded Successfully!</b>\n\nTrip: <b>{trip}</b>\n"
              "Files: {count}\nType: <b>{mode}</b>\nFile: {filename}",
        "hi": "✅ <b>POD सफलतापूर्वक अपलोड हो गई!</b>\n\nTrip: <b>{trip}</b>\n"
              "फाइलें: {count}\nType: <b>{mode}</b>\nFile: {filename}",
    },
    "pod_upload_failed_retry": {
        "en": "❌ POD upload failed.\nError: {error}\n\nPlease try again or contact ops staff.",
        "hi": "❌ POD अपलोड असफल।\nError: {error}\n\nफिर से कोशिश करें या ops staff से संपर्क करें।",
    },
    "what_next": {
        "en": "What next?",
        "hi": "अब क्या करें?",
    },
    "download_pdf_failed": {
        "en": "⚠️ Could not download PDF. Please resend.",
        "hi": "⚠️ PDF डाउनलोड नहीं हो पाई। कृपया फिर से भेजें।",
    },
    "qr_not_detected": {
        "en": "⚠️ QR not detected in this PDF.\n\n"
              "Please ensure the cover-page QR is visible and resend, "
              "or send /start and use a photo instead.",
        "hi": "⚠️ इस PDF में QR नहीं मिला।\n\n"
              "कृपया कवर-पेज का QR साफ दिखाएं और फिर से भेजें, "
              "या /start भेजकर फोटो का उपयोग करें।",
    },
    "pod_already_uploaded": {
        "en": "⚠️ <b>POD Already Uploaded!</b>\n\nTrip: <b>{trip}</b>\nStatus: <b>{status}</b>\n\n"
              "What do you want to do?",
        "hi": "⚠️ <b>POD पहले से अपलोड है!</b>\n\nTrip: <b>{trip}</b>\nStatus: <b>{status}</b>\n\n"
              "आप क्या करना चाहते हैं?",
    },
    "btn_replace_original": {
        "en": "🔄 Replace Original",
        "hi": "🔄 ओरिजिनल बदलें",
    },
    "btn_upload_duplicate": {
        "en": "📋 Upload Duplicate",
        "hi": "📋 डुप्लिकेट अपलोड करें",
    },
    "btn_cancel_exit": {
        "en": "🚪 Cancel",
        "hi": "🚪 रद्द करें",
    },
    "pod_upload_success_simple": {
        "en": "✅ <b>POD Uploaded Successfully!</b>\n\nTrip: <b>{trip}</b>\nFile: {filename}",
        "hi": "✅ <b>POD सफलतापूर्वक अपलोड हो गई!</b>\n\nTrip: <b>{trip}</b>\nFile: {filename}",
    },
    "pod_upload_failed_simple": {
        "en": "❌ POD upload failed.\nError: {error}",
        "hi": "❌ POD अपलोड असफल।\nError: {error}",
    },
    "ocr_extract_failed": {
        "en": "⚠️ Could not extract data from this PDF.\nEnsure it's the TCN Summary Sheet and resend.",
        "hi": "⚠️ इस PDF से डेटा नहीं निकाला जा सका।\nसुनिश्चित करें कि यह TCN Summary Sheet है और फिर से भेजें।",
    },
    "ocr_review_card": {
        "en": "📋 <b>Extracted Trip Data — Please Review</b>\n\n"
              "TCN No     : <code>{tcn_no}</code>\n"
              "Date       : {date}\n"
              "Vehicle    : {vehicle}\n"
              "Origin     : {origin}\n"
              "Destination: {destination}\n"
              "Customer   : {customer}\n"
              "Vendor     : {vendor}\n"
              "LR No      : {lr_no}\n"
              "Packages   : {packages}\n\n"
              "⚠️ <i>Trip will be saved as Draft. Open Desk to complete and submit.</i>",
        "hi": "📋 <b>निकाला गया Trip डेटा — कृपया जांचें</b>\n\n"
              "TCN No     : <code>{tcn_no}</code>\n"
              "Date       : {date}\n"
              "Vehicle    : {vehicle}\n"
              "Origin     : {origin}\n"
              "Destination: {destination}\n"
              "Customer   : {customer}\n"
              "Vendor     : {vendor}\n"
              "LR No      : {lr_no}\n"
              "Packages   : {packages}\n\n"
              "⚠️ <i>Trip Draft के रूप में सेव होगी। पूरा करने और सबमिट करने के लिए Desk खोलें।</i>",
    },
    "btn_create_draft_trip": {
        "en": "✅ Create Draft Trip",
        "hi": "✅ Draft Trip बनाएं",
    },
    "btn_cancel_x": {
        "en": "❌ Cancel",
        "hi": "❌ रद्द करें",
    },
    "pod_upload_success_merged": {
        "en": "✅ <b>POD Uploaded Successfully!</b>\n\nTrip: <b>{trip}</b>\n"
              "Photos merged: {count}\nType: <b>{mode}</b>\nFile: {filename}",
        "hi": "✅ <b>POD सफलतापूर्वक अपलोड हो गई!</b>\n\nTrip: <b>{trip}</b>\n"
              "फोटो मर्ज हुई: {count}\nType: <b>{mode}</b>\nFile: {filename}",
    },
    "pod_generation_failed": {
        "en": "❌ POD generation failed.\nError: {error}\n\nPlease contact ops staff.",
        "hi": "❌ POD जेनरेशन असफल।\nError: {error}\n\nकृपया ops staff से संपर्क करें।",
    },
    "pending_images_failed": {
        "en": "⚠️ Could not save pending photos. Please resend.",
        "hi": "⚠️ पेंडिंग फोटो सेव नहीं हो पाई। कृपया फिर से भेजें।",
    },
    "pending_images_saved": {
        "en": "📎 {count} photo(s) uploaded for Trip <b>{trip}</b>.\n"
              "Send more or tap <b>Complete POD</b> when done.",
        "hi": "📎 Trip <b>{trip}</b> के लिए {count} फोटो अपलोड हो गई।\n"
              "और भेजें या पूरा होने पर <b>Complete POD</b> दबाएं।",
    },
    "mode_original": {
        "en": "Original",
        "hi": "ओरिजिनल",
    },
    "mode_original_replaced": {
        "en": "Original (Replaced)",
        "hi": "ओरिजिनल (बदला गया)",
    },
    "mode_duplicate": {
        "en": "Duplicate",
        "hi": "डुप्लिकेट",
    },

    # ── collection keyboard / resume buttons ────────────────────────────────
    "btn_img_n": {
        "en": "🔄 Photo {seq} uploaded",
        "hi": "🔄 फोटो {seq} अपलोड हो गई",
    },
    "btn_upload_image_n": {
        "en": "📤 Upload Next Photo",
        "hi": "📤 अगली फोटो अपलोड करें",
    },
    "btn_complete_pod": {
        "en": "✅ Complete POD",
        "hi": "✅ POD पूरा करें",
    },
    "btn_add_photos_resume": {
        "en": "📷 Add Photos — {trip} ({count} photo)",
        "hi": "📷 फोटो जोड़ें — {trip} ({count} फोटो)",
    },
    "btn_complete_pod_resume": {
        "en": "✅ Complete POD — {trip} ({count} photo)",
        "hi": "✅ POD पूरा करें — {trip} ({count} फोटो)",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Return the translated string for `key` in `lang`, formatted with kwargs."""
    entry = TEXT.get(key)
    if not entry:
        return key
    template = entry.get(lang) or entry.get(DEFAULT_LANG, key)
    return template.format(**kwargs) if kwargs else template


def get_lang(session) -> str:
    """Return the language code stored on a Telegram Session document."""
    return getattr(session, "language", None) or DEFAULT_LANG


def get_lang_by_chat(chat_id: str) -> str:
    """Look up the language for a chat_id without loading the full session doc."""
    return frappe.db.get_value("Telegram Session", chat_id, "language") or DEFAULT_LANG
