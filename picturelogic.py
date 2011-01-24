import gtk
import gtk.gdk
import gobject
import sys
from core import pictures
import logging
import config

# create logger
logger = logging.getLogger("picturelogic")


    
class PictureLogic:
    def close(self, widget):
        logger.info("Exiting picturelogic")
        gtk.main_quit()
        
          
    def __init__(self):
          
          self.builder = gtk.Builder()
          self.builder.add_from_file("gui/gui.glade")
          self.window = self.builder.get_object("window1")
          self.window.show()
          self.addTagsDialog = self.builder.get_object("addtags_dialog")
          dic = {
                 "on_quit_menuitem_activate" : self.close,
                 "on_about_menuitem_activate" : self.about,
                 "on_import_folder_activate": self.importFolder,
                 "on_importfolder_ok_button_clicked": self.doImportFolder,
                 "on_open_image_activate": self.openImage,
                 "on_search_button_clicked" : self.search,
                 "on_pictures_iconview_item_activated" : self.iconview_item_activated,
                 "on_pictures_iconview_selection_changed" : self.iconview_selection_changed,
                 "on_pictures_iconview_button_press_event": self.iconview_button_press_events,
                 "on_addtags_cancel_button_clicked": self.addTagsDialog_destroy,
                 "on_addtags_ok_button_clicked": self.doAddTags
                 }
          self.builder.connect_signals(dic)
          # Initialise IconView and Pictures Store
          self.iconView = self.builder.get_object("pictures_iconview")
          self.pictures_store = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT)
          self.iconView.set_model(self.pictures_store)
          self.iconView.set_pixbuf_column(0)
          self.iconView.set_text_column(1)
 
          self.tagsTree = gtk.TreeView()
          self.tagsTree.connect("cursor-changed", self.refresh_pictures_on_tag_selected)
          self.refresh_all_pictures()
          self.buildTagsTree()
    def refresh_all_pictures(self):
         self.pictures = pictures.get_pictures_from_db()
         self.refresh_pictures()
    def refresh_pictures_on_tag_selected(self, widget):
        iter = self.tagsTree.get_selection().get_selected()[1]
        logger.debug(iter)
        value_selected = self.tagsStore.get_value(iter, 0)
        logger.debug("tags tree column 0: " + self.tagsTree.get_column(0).get_title())
        if iter == None or value_selected == self.tagsTree.get_column(0).get_title():
            self.refresh_all_pictures()
            return        
        logger.debug("Tag selected: " + value_selected)
        tagname = self.tagsStore.get_value(iter, 0)
        self.pictures = pictures.get_pictures_with_tag(tagname)
        picture_names = ""
        for picture in self.pictures:
            picture_names += picture[2] + ", "
        logger.debug("pictures with tag: " + tagname + " are: " + picture_names)
        
        self.refresh_pictures()
          
    def about(self, widget):
        self.about = About(self.builder)
        
    def importFolder(self, widget):
        self.importFolderDialog = self.builder.get_object("importfolderdialog")
        self.importFolderDialog.show()
    def doImportFolder(self, widget):
        
        self.folder = self.importFolderDialog.get_filename()
        logger.debug("Import all pictures from folder: " + self.folder)
        # Close import dialog
        self.importFolderDialog.hide()
        #1 Import images from folder recursively
        
        pictures.import_from_folder(self.folder)
        
        #2 Display images using gtk icon view
        self.pictures = pictures.get_pictures_from_db()
        self.refresh_pictures()
        self.buildTagsTree()
    def openImage(self, widget):
        self.openImageDialog = self.builder.get_object("openimagedialog")
        self.openImageDialog.show()
    def refresh_pictures(self):                       
        if self.pictures == []:
            return
        logger.debug("Refreshing pictures")       
        self.pictures_store.clear()
        for picture in self.pictures:
            logger.debug("Adding " + picture[2])
            pixbuf = gtk.gdk.pixbuf_new_from_file(picture[0])
            picture_caption = ''
            picture_tags = pictures.get_tags_for_picture(picture[3])
            logger.debug(picture_tags)
            if picture_tags != []:
                picture_caption = ",".join(picture_tags)
            self.pictures_store.append([pixbuf, picture_caption, picture[0], picture[3]])
        self.iconView.show_all()
        
    def search(self, widget):
        text = self.builder.get_object("entry_search").get_text()
        logger.debug("Text selected: " + text)
        if text != '': 
            self.pictures = pictures.search_pictures_by_text(text)
            picture_names = ""
            for picture in self.pictures:
                picture_names += picture[2] + ", "
            logger.debug("pictures with tag: " + text + " are: " + picture_names)
            self.refresh_pictures()
      
    
    def iconview_item_activated(self, widget, item):
        logger.debug("item activated: " + self.pictures_store[item][1])
        pass
    
    def iconview_selection_changed(self, widget):
        items = self.iconView.get_selected_items()
        self.exif_label = self.builder.get_object('exif_label')
        for item in items:
            logger.debug("item selected: " + self.pictures_store[item][1])
        # If there is only one item selected, display exif.
        label_str = ''
        if len(items) == 1:
            item = items[0]
            picture = self.pictures[item[0]]
            label_str += 'File: ' + picture[2] + '\n'
            exif = pictures.parse_db_exif(picture[6])
            print exif
            for k in exif:
               label_str += k + ':' + exif[k] + '\n'
            
            self.exif_label.set_text(label_str)
        
        
    def iconview_button_press_events(self, widget, event):      
        item = self.iconView.get_path_at_pos(event.x, event.y)
        if (event.button == 3 and item != None):  
          logger.debug("item where right click ocurred: " + self.pictures_store[item][1])
          self.iconView.select_path(item)
          self.iconMenu = gtk.Menu()
          addTagsItem = gtk.MenuItem("Add tags")
          addTagsItem.connect("activate", self.addTags)
          removeTagsItem = gtk.MenuItem("Remove tags")
          self.iconMenu.append(addTagsItem)
          self.iconMenu.append(removeTagsItem)
          self.iconMenu.popup(None, None, None, event.button, event.time, None)
          self.iconMenu.show_all()
    def addTags(self, widget):
        self.addTagsDialog.show()
        
    def doAddTags(self, widget):
        logger.debug("Adding tags to pictures selected")
        selectedItems = self.iconView.get_selected_items()
        pictureids = []
        for item in selectedItems:
            pictureids.append(self.pictures_store[item][3])
        addtagsEntry = self.builder.get_object("addtags_entry")
        selectedTags = addtagsEntry.get_text()
        if selectedTags != '':
            pictures.insert_tags(pictureids, selectedTags)
        self.addTagsDialog_destroy(self, widget)
        self.refresh_tags_tree()
        self.refresh_pictures()
    def addTagsDialog_destroy(self, widget, event):
        logger.debug("Destroying add tags dialog")
        self.addTagsDialog.destroy()
    def buildTagsTree(self):
        logger.debug("Building Tags Tree")
        self.treeWindow = self.builder.get_object("tree_swindow")
        self.tagsStore = gtk.TreeStore(str)
        root = self.tagsStore.append(None, ["Tags"])
        tags = pictures.get_tags_from_db()
        if tags == []:
            return
        for tagname in tags:
            logger.debug("appending tag to tree: " + tagname[0])
            self.tagsStore.append(root, tagname)
       
        self.tagsTree.set_model(self.tagsStore)
        column = gtk.TreeViewColumn("Tags")
        cell = gtk.CellRendererText()
        self.tagsTree.append_column(column)
        column.pack_start(cell, False)
        column.add_attribute(cell, "text", 0)
        if self.tagsTree in self.treeWindow.get_children():
            self.treeWindow.remove(self.tagsTree)
        self.treeWindow.add(self.tagsTree)
        self.tagsTree.show_all() 
        
    def refresh_tags_tree(self):
        logger.debug("refreshing tags tree")
        self.tagsStore.clear()
        root = self.tagsStore.append(None, ["Tags"])
        tags = pictures.get_tags_from_db()
        if tags == []:
            return
        for tagname in tags:
            logger.debug("appending tag to tree: " + tagname[0])
            self.tagsStore.append(root, tagname)
        
               
        
class About:
    
    def __init__(self, builder):
        
        self.window = builder.get_object("aboutdialog")
        self.window.show()
            
print sys.path    
PictureLogic()
gtk.main()   
    
