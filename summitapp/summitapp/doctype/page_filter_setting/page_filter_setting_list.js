// frappe.listview_settings['Page Filter Setting'] = {
//     onload: function (listview) {
//         listview.page.add_menu_item('Update Filters', function(event){
//             frappe.call({
//                 method: "summitapp.summitapp.doctype.page_filter_setting.page_filter_setting.update_filters",
//                 type: "POST",
//                 callback: function(r) {
//                     console.log("Success");
//                     location.reload();
//                     }
//                 })

//         });
//      }
// }