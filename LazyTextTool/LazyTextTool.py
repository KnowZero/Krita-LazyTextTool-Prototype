from PyQt5 import QtCore, QtGui, QtWidgets, uic
from krita import *
from .LazyTextToolFunc import *
import re


class LazyTextTool(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.currentTool = None
        self.currentLayer = None
        self.currentDocument = None
        self.currentTextCanvas = None
        self.canvas = None
        self.active = False
        self.toolboxButtonFilterItem = None
        self.onTab = 0
        self.kritaVersion = int(Krita.instance().version().split(".")[0])
        self.screenDPI = QtGui.QGuiApplication.screens()[0].logicalDotsPerInch()
        #self.bindToolButton()

    class toolboxButtonFilter(QtWidgets.QToolButton):
        def __init__(self, textTool=None, parent=None):
            super(LazyTextTool.toolboxButtonFilter, self).__init__(parent)
            self.textTool = textTool

        def eventFilter(self, obj, event):
            if self.textTool.active:
                if event.type() == 12:
                    if obj.isChecked():
                        print ("OPEN CANVAS FROM FILTER")
                        LazyTextTool.openTextCanvas(self.textTool)
                    else:
                        if self.textTool.currentTextCanvas is not None:
                            self.textTool.currentTextCanvas.writeItem(self.textTool.currentTextCanvas.scene.selectedObject)
                        LazyTextTool.closeTextCanvas(self.textTool)
            return False
        
    class layerListFilter(QtWidgets.QTreeView):
        def __init__(self, textTool=None, parent=None):
            super(LazyTextTool.layerListFilter, self).__init__(parent)
            self.textTool = textTool
            
        def eventFilter(self, obj, event):
            if event.type() == 207 or event.type() == 51:
                LazyTextTool.setCurrentLayer(self.textTool)
            return False

    class TextCanvas(QtWidgets.QWidget):
        def __init__(self, textTool=None, parent=None):
            super(LazyTextTool.TextCanvas, self).__init__(parent)
            self.textTool = textTool
            self.wheelZoomCounter = 0
            
            self.writeItemQueue = None
            self.selectedAlienItem = None
           
            self.scene = LazyTextScene(self)
            currentDocument = self.textTool.currentDocument
            self.scene.canvasResolution = currentDocument.resolution()
            self.scene.canvasBaseZoomLevel = Krita.instance().activeWindow().activeView().canvas().zoomLevel()
            self.view = LazyTextView(self.scene)
            
            
            self.gridLayout = QtWidgets.QGridLayout(self);
            self.gridLayout.setSpacing(0);
            self.gridLayout.setContentsMargins(0, 0, 0, 0);
            self.gridLayout.addWidget(self.view)
            self.helperDialog = LazyTextHelper(self)

            self.show()
        
        def fillLayer(self, layer, shapes):
            for shape in shapes:
                self.textObjectFromLayerAndShape([ layer, shape ])
            
        def textObjectFromLayerAndShape(self, textItem):
            textObject = LazyTextObject()
            docRes = self.scene.canvasResolution
            textObject.layer = textItem[0]
            textObject.shape = textItem[1]
            
            r = QtCore.QRectF()
            
            position = [0,0]
            #position = [LazyTextUtils.ptsToPx(textItem[1].position().x(), docRes), LazyTextUtils.ptsToPx(textItem[1].position().y(), docRes)  ]
            
            if self.textTool.kritaVersion < 5:
                position = [LazyTextUtils.ptsToPx(textItem[1].position().x(), docRes), LazyTextUtils.ptsToPx(textItem[1].position().y(), docRes)  ]
                r = QtCore.QRectF(
                        position[0],
                        position[1],
                        
                        LazyTextUtils.ptsToPx(textItem[1].boundingBox().width(), docRes),
                        LazyTextUtils.ptsToPx(textItem[1].boundingBox().height(), docRes)
                )
            else:
                r = QtCore.QRectF(
                        position[0],
                        position[1],
                        
                        textItem[1].boundingBox().width(),
                        textItem[1].boundingBox().height()
                ) 
                   
            svgContent = textItem[1].toSvg(False,False) if self.textTool.kritaVersion >= 5 else textItem[1].toSvg()
            #this is a temp fix that should be changed:
            svgContent = svgContent.replace(' krita:',' krita_')
                    
            print ("SVG", svgContent)

            #blockSettings = []
                    

            docContent = LazyTextUtils.svgToDocument(svgContent)
            
            if docContent[1]['version'] == 0 and textItem[1].name() is not None:
                docData = re.search(r'^t(\d)_(\d+)_(\d)([\d\.]+)_(.+)$', textItem[1].name())
                if docData is not None:
                    docContent[1]['version']=int(docData.group(1))
                    docContent[1]['resolution']=int(docData.group(2))
                    docContent[1]['wrapmode']=int(docData.group(3))
                    docContent[1]['boundarywidth']=float(docData.group(4))
                    docContent[1]['crc32']=docData.group(5)
            
            self.scene.addItem(textObject)
            textObject.finalizeObject(docContent, r)
            textObject.textItem.disableEditing()
            textObject.textItem.setOpacity(0)
            
            if self.textTool.kritaVersion >= 5:
                t = textItem[1].transformation()
                print ("POS TEST", [LazyTextUtils.ptsToPx(textItem[1].position().x(), docRes), LazyTextUtils.ptsToPx(textItem[1].position().y(), docRes)  ], [ LazyTextUtils.ptsToPx(t.dx(), docRes), LazyTextUtils.ptsToPx(t.dy(), docRes) ]  )
                print("transformdata", docContent[1]['transform'], [  t.m11(), t.m12(), t.m21(), t.m22(), t.dx(), t.dy() ] )
                
                m = list(map(lambda x: LazyTextUtils.ptsToPx(x, docRes) ,[t.m11(), t.m12(), t.m21(), t.m22(), t.dx(), t.dy() ]))
                
                print ("MYNEWHEIGHT1=",t.dy(), m[5])
                textObject.setTransform( QtGui.QTransform( m[0], m[1], m[2], m[3], 
                                                          #LazyTextUtils.ptsToPx(textItem[1].position().x(), docRes),LazyTextUtils.ptsToPx(textItem[1].position().y(), docRes)
                                                          m[4], m[5] 
                                                          #0,0
                                                          ) )
                # boundry border probably doesn't match the transformation

            return textObject
            
        def selectAlienItemAt(self, mousePoint):
            
            currentDocument = self.textTool.currentDocument
            docRes = currentDocument.resolution()
            selectedItem = None
            
            # all these functions use points, not pixels
            alienTextItem = self.findSingleTextAt( QtCore.QPointF( LazyTextUtils.pxToPts(mousePoint.x(),docRes), LazyTextUtils.pxToPts(mousePoint.y(),docRes) )  )
            
            print ("ALIEN ITEM RES", alienTextItem)
            
            if alienTextItem is not None:
                #tempItem = LazyTextTempBox(self.scene)
                #tempItem.setRect(alienTextItem[1].boundingBox())
                #tempItem.tempRectData = QtCore.QRectF( alienTextItem[1].pos(), QtCore.QPointF(alienTextItem[1].boundingBox().x(),alienTextItem[1].boundingBox().x()) )
                #tempItem.tempSvgData = alienTextItem[1].toSvg()
                
                #self.scene.addItem(tempItem)

                
                textItemList = self.findAllTextInLayer(alienTextItem[0])
                
                for textItem in textItemList:
                    if alienTextItem[1].boundingBox() == textItem[1].boundingBox(): self.textTool.resetCurrentLayer()
                    textObject = self.textObjectFromLayerAndShape(textItem)
                    
                    #font = textObject.textItem.font()
                    #fontMetrics = QtGui.QFontMetricsF(font)
                    
                    #textObject.setRect( textObject.rect().adjusted(0, LazyTextUtils.ptsToPx(fontMetrics.ascent()*-1,  docRes) ,0,0) )
                    #textObject.textItem.setPos(textObject.rect().topLeft())
                    
                    #>>self.helperDialog = LazyTextHelper(textObject.textItem, self)
                    #>>self.helperDialog.show()
                    
                    print ("IS SAME SHAPE", alienTextItem[1].boundingBox(), textItem[1].boundingBox())
                    if alienTextItem[1].boundingBox() == textItem[1].boundingBox():
                        selectedItem = textObject
                    #>>    textObject.textItem.setOpacity(0)
                    
                #alienTextItem[0].setVisible(False)
                self.selectedAlienItem = {'item':selectedItem, 'shape':alienTextItem[1], 'layer':alienTextItem[0] }                
                self.textTool.currentDocument.setActiveNode(alienTextItem[0])
                currentDocument.refreshProjection()

                return {'item':selectedItem, 'shape':alienTextItem[1], 'layer':alienTextItem[0] }

            return None  
            


        def findSingleTextAt(self, mousePoint):
            return self.findSingleTextInGroup(mousePoint, self.textTool.currentDocument.activeNode().parentNode().childNodes())
           
        
        def findSingleTextInGroup(self, mousePoint, layerNodeList):
            shape = None
            for nodeLayer in layerNodeList:
                if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible():
                    shape = self.findSingleTextInLayer(nodeLayer, mousePoint)
                elif nodeLayer.type() == 'grouplayer' and nodeLayer.visible() and len(nodeLayer.childNodes()) > 0:
                    shape = self.findSingleTextInGroup(mousePoint, nodeLayer.childNodes())
                    
                if shape is not None:
                    return shape

            return None


        def findSingleTextInLayer(self, nodeLayer, mousePoint):
            if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible() and (self.textTool.kritaVersion >= 5 or len(nodeLayer.shapes()) == 1):
                for shape in nodeLayer.shapes():
                    if shape.type() == 'KoSvgTextShapeID' and shape.boundingBox().contains(mousePoint):
                        return [nodeLayer, shape]
            return None            
        
        def findTextAt(self, mousePoint):
            return self.findTextInGroup(mousePoint, self.textTool.currentDocument.activeNode().parentNode().childNodes())
            #return self.findTextInGroup(mousePoint, self.textTool.currentDocument.rootNode().childNodes())
           
        
        def findTextInGroup(self, mousePoint, layerNodeList):
            shape = None
            
            for nodeLayer in layerNodeList:
                if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible():
                    shape = self.findTextInLayer(nodeLayer, mousePoint)
                elif nodeLayer.type() == 'grouplayer' and nodeLayer.visible() and len(nodeLayer.childNodes()) > 0:
                    shape = self.findTextInGroup(mousePoint, nodeLayer.childNodes())
                    
                if shape is not None:
                    return [nodeLayer, shape]

            return None


        def findTextInLayer(self, nodeLayer, mousePoint):
            if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible():
                for shape in nodeLayer.shapes():
                    if shape.type() == 'KoSvgTextShapeID' and shape.boundingBox().contains(mousePoint):
                        return shape
            return None
        
        
        def findAllTextInGroup(self, layerNodeList = None):
            if layerNodeList is None:
                layerNodeList = self.textTool.currentDocument.rootNode().childNodes()

            textShapeList = []
            
            for nodeLayer in layerNodeList:
                if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible():
                    textShapeList += self.findAllTextInLayer(nodeLayer)
                elif nodeLayer.type() == 'grouplayer' and nodeLayer.visible() and len(nodeLayer.childNodes()) > 0:
                    textShapeList += self.findAllTextInGroup(nodeLayer.childNodes())
  
            return textShapeList       
        
        def findAllTextInLayer(self, nodeLayer):
            textShapeList = []
            
            if nodeLayer.type() == 'vectorlayer' and nodeLayer.visible():
                for shape in nodeLayer.shapes():
                    if shape.type() == 'KoSvgTextShapeID':
                        textShapeList.append([nodeLayer,shape])
            return textShapeList

        def sceneWheelEvent(self, event):
            pass
            
        def viewWheelEvent(self, event):
            
            self.wheelZoomCounter += abs(event.angleDelta().y()/2)
            
            if self.wheelZoomCounter >= abs(event.angleDelta().y()):
                self.wheelZoomCounter = 0
                if event.angleDelta().y() > 0:
                    Krita.instance().action('view_zoom_in').trigger()
                else:
                    Krita.instance().action('view_zoom_out').trigger()

        
        def cleanup(self):
            self.scene.cleanup()
        
        def cancelItem(self, textObject):
            self.textTool.resetCurrentLayer()
            currentLayer = self.textTool.currentLayer
            if self.scene.modifyMode and currentLayer.type() == 'vectorlayer':
                if self.textTool.kritaVersion >= 5:
                    textObject.shape.setVisible(True)
                    textObject.shape.update()
                
                elif currentLayer.visible() is False and len(currentLayer.shapes()) == 1:
                    currentLayer.setVisible(True)
                self.textTool.currentDocument.refreshProjection()
                shapes = currentLayer.shapes()
                self.fillLayer(currentLayer, shapes)
        
        def editItem(self, textObject):
            print ("EDIT ITEM1")
            self.textTool.setCurrentLayer()
            currentLayer = self.textTool.currentLayer
            
            self.helperDialog.showFor(textObject.textItem, self.scene.modifyMode == False)
            
            #self.helperDialog.move( textObject.pos().toPoint() )
            #self.helperDialog.move( self.view.mapToGlobal(QtCore.QPoint(0, 0)) )
            #if self.scene.modifyMode:
            #    self.editItemQueue
            
            if self.scene.modifyMode and currentLayer.type() == 'vectorlayer' and currentLayer.visible():
                if self.textTool.kritaVersion >= 5:
                    textObject.shape.setVisible(False)
                    textObject.shape.update()
                elif len(currentLayer.shapes()) == 1:
                    currentLayer.setVisible(False)
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.IBeamCursor)
                self.textTool.currentDocument.refreshProjection()
            print ("EDIT ITEM2", currentLayer.type())
            
        def writeItem(self, textObject):
            currentDocument = self.textTool.currentDocument
            currentLayer = self.textTool.currentLayer
            
            if textObject.textItem.toPlainText() == '':
                self.helperDialog.target = None
                self.scene.removeItem(textObject)
                if self.scene.modifyMode and currentLayer.type() == 'vectorlayer':
                    if self.textTool.kritaVersion >= 5:
                        textObject.shape.remove()
                    elif currentLayer.visible() is False and len(currentLayer.shapes()) == 1:
                        currentLayer.remove()
                        currentDocument.refreshProjection()
                print ("REMOVED BLANK")
                return
            
          
            t = textObject.transform()
            st = textObject.sceneTransform()
            sp = textObject.scenePos()
            p = textObject.rect()
            print ("SCENE TRANSFORM", st.dx(), st.dy(), "DTRANSFORM", st.dx(), st.dy(), "SCENE POS", sp.x(), sp.y(), "RPOS", p.x(), p.y() )
            
            
            print ("CHECK NEW LAYER!", currentLayer.type(), currentLayer.visible())
            
            if currentLayer.type() == 'vectorlayer':
                print ("CHECK NEW LAYER2!", len(currentLayer.shapes()) )
            
            writeItemQueue = { 'item': textObject, 'document': currentDocument, 'layer': currentLayer, 'remove_layer': None }

            print ("TRY NEW LAYER!")
            if currentLayer.type() == 'grouplayer':
                parentLayer = currentLayer
            else:
                parentLayer = currentLayer.parentNode()
                

            if self.textTool.kritaVersion >= 5 and (self.scene.modifyMode or self.scene.appendMode):
                self.finishWriteItem(writeItemQueue)
                
                
            else:
                if self.scene.modifyMode:
                    writeItemQueue['remove_layer'] = currentLayer
                newLayer = currentDocument.createVectorLayer('LazyText Work Layer')
                
                writeItemQueue['layer'] = newLayer
                self.writeItemQueue = writeItemQueue
                parentLayer.addChildNode(newLayer, (None if currentLayer.type() == 'grouplayer' else currentLayer) )
                currentDocument.setActiveNode(newLayer)

            self.helperDialog.hideDialog()

            '''
            if currentLayer.type() == 'vectorlayer' and currentLayer.visible() == False and len(currentLayer.shapes()) == 1 and self.scene.modifyMode:
                print ("TRY NEW LAYER!")
                parentLayer = currentLayer.parentNode()
                
                #Krita.instance().action('add_new_shape_layer').trigger()
                #currentDocument.waitForDone()
                #self.waitForNewLayer = QtCore.QEventLoop()
                
                #print ("WAIT FOR NEW LAYER!", self.waitForNewLayer)
                
                writeItemQueue['remove_layer'] = currentLayer
                
                
                newLayer = currentDocument.createVectorLayer('LazyText Work Layer')
                
                writeItemQueue['layer'] = newLayer
                self.writeItemQueue = writeItemQueue
                parentLayer.addChildNode(newLayer, None)
                currentDocument.setActiveNode(newLayer)
                #returnCode = self.waitForNewLayer.exec()
                #print ("RETURN CODE", returnCode)
                #self.waitForNewLayer = None
                return 2
            else:
                self.finishWriteItem(writeItemQueue)
                return 1
            '''
            
            '''
            opts = { 
                    'x' : textObject.textItem.scenePos().x(), 
                    'y' : textObject.textItem.scenePos().y(),
                    'resolution' : currentDocument.resolution(),
                    'ascent' : textObject.textItem.defaultFontMetrics.ascent()
            }
            '''
            

                
        def finishWriteItem(self, writeItemQueue):
            textObject = writeItemQueue['item']
            currentDocument = writeItemQueue['document']
            currentLayer = writeItemQueue['layer']
            removeLayer = writeItemQueue['remove_layer']
            
            blockSettings = LazyTextUtils.loadBlockSettings(textObject.textItem.document())
            

            opts = {
                        'x' : textObject.textItem.scenePos().x(), 
                        'y' : textObject.textItem.scenePos().y(),
                        'resolution' : currentDocument.resolution(),
                        'ascent' : blockSettings[0]['ascent'],
                        'blockSettings' : blockSettings,
                        #'width': LazyTextUtils.pxToPts(opts['width'], currentDocument.resolution()),
                        'width': textObject.textItem.document().textWidth(),
                        'wrap' : textObject.textWrapMode,
                        'unique' : textObject.textItem.toPlainText() + str(textObject.rect().width()),
                        'transform': None,
                        #'transform': textObject.sceneTransform() if self.scene.modifyMode else None,
            }
            
            if self.textTool.kritaVersion >= 5:
                opts['transform']=textObject.transform() if self.scene.modifyMode else None


            doc = textObject.textItem.document()
            tcursor=textObject.textItem.textCursor()
            textContent = textObject.textItem.toPlainText()
            textObject.textItem.setOpacity(0)
        
            for bi in range(len(blockSettings)-1,-1,-1):
                for li in range(len(blockSettings[bi]['lines'])-1,0,-1):
                    tcursor.setPosition(blockSettings[bi]['start']+blockSettings[bi]['lines'][li]['start'])
                    tcursor.insertText('<br data-wordwrap="true" />')
                
                
            
            textContent=textContent.replace("\n", " ")
            htmlContent = textObject.textItem.toHtml()
            print ("PREOUT HTML", htmlContent)
            htmlContent = htmlContent.replace('<br />&lt;br data-wordwrap=&quot;true&quot; /&gt;','<br data-wordwrap="true" />')
            htmlContent = htmlContent.replace('&lt;br data-wordwrap=&quot;true&quot; /&gt;','<br data-wordwrap="true" />')
            htmlContent = re.sub(r'(<p[^>]*?>)<br /></p>',r'\1 </p>', htmlContent)

            
            print ("OUT HTML", htmlContent)
            
            if textContent != '':
                svgItem = LazyTextUtils.htmlToSvg(htmlContent, opts )
                svgContent = LazyTextUtils.svgDocument(svgItem, currentDocument.width(), currentDocument.height(), currentDocument.resolution() )
                print ("OUT SVG", svgContent)
                shapes = self.writeSvgContent(svgContent, currentLayer)
                currentDocument.waitForDone()
                
                
                if self.textTool.kritaVersion >= 5:
                    if self.scene.modifyMode: textObject.shape.remove()
                    self.scene.removeItem(textObject)
                    if self.scene.modifyMode or self.scene.appendMode: 
                        self.textObjectFromLayerAndShape( [currentLayer, shapes[0]] )
                    else:
                        self.textTool.resetCurrentLayer()
                    #textObject.layer = currentLayer
                    #textObject.shape = shapes[0]
                else:
                    self.textTool.resetCurrentLayer()
                    
                
                print ("APPEND MODE:", self.scene.appendMode, len(currentLayer.shapes()) )
                if not self.scene.appendMode and len(currentLayer.shapes()) <= 1: currentLayer.setName( re.search('^(.{1,50})',textContent).group(1) )
                currentDocument.refreshProjection()
                
            self.helperDialog.target = None
            #???textObject.textItem.setOpacity(0)
            #self.scene.removeItem(textObject)
            if removeLayer is not None:
                removeLayer.remove()
            
        def writeSvgContent(self, svgContent, layer):
            if self.textTool.kritaVersion >= 5:
                return layer.addShapesFromSvg(svgContent)
            else:
                mimeOldContent=QtGui.QGuiApplication.clipboard().mimeData();
                mimeStoreContent=QtCore.QMimeData() 
                for mimeType in mimeOldContent.formats(): 
                    mimeStoreContent.setData(mimeType,QtCore.QByteArray(mimeOldContent.data(mimeType))) 
        
                mimeNewContent=QtCore.QMimeData()
                mimeNewContent.setData('image/svg', svgContent.encode())
                #print ("mime",mimeOldContent)
                QtGui.QGuiApplication.clipboard().setMimeData(mimeNewContent)
                #print ("mime2",mimeOldContent)
                Krita.instance().action('edit_paste').trigger()
                QtGui.QGuiApplication.clipboard().setMimeData(mimeStoreContent)
                return None
            
    def resetCurrentLayer(self):
        self.setCurrentLayer()
        
        if self.currentTextCanvas is not None:
            self.currentTextCanvas.cleanup()
            self.canvasAdjust()

    def setCurrentLayer(self):
        self.currentDocument = Krita.instance().activeDocument()
        self.currentLayer = self.currentDocument.activeNode()
        
 


    def closeTextCanvas(self, soft = False):
        if self.currentTextCanvas is not None:
            self.currentTextCanvas.cleanup()
            self.currentTextCanvas.close()
            self.currentTextCanvas = None
            self.unbindScrollArea()
            if soft == False: self.unbindLayerList2()
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QApplication.restoreOverrideCursor()
            

    def openTextCanvas(self):
        if self.currentTextCanvas is None:
            qwin = Krita.instance().activeWindow().qwindow()
            centralWidget = qwin.centralWidget()
            if centralWidget is not None:
                self.mdi = centralWidget.findChild(QtWidgets.QMdiArea)
            else:
                for win in QtWidgets.QApplication.topLevelWidgets():
                    winName = win.objectName()
                    if winName.startswith('MainWindow'):
                        mdi = win.findChild(QtWidgets.QMdiArea)
                        if mdi:
                            self.mdi = mdi
                            break;
            
            subWindow = self.mdi.activeSubWindow()
            onTab = self.mdi.findChild(QtWidgets.QTabBar)
            
            if onTab:
                self.onTab = onTab.currentIndex()
            else:
                tabs = [ idx for idx, obj in enumerate(self.mdi.subWindowList()) if obj is subWindow ]
                self.onTab = tabs[0]

            self.scrollArea = subWindow.findChild(QtWidgets.QAbstractScrollArea)
            self.resetCurrentLayer()
            self.currentTextCanvas = self.TextCanvas(self,self.scrollArea)
            self.currentTextCanvas.resize(self.scrollArea.rect().width(),self.scrollArea.rect().height())
            self.canvasAdjust()
            self.bindScrollArea()
            self.bindLayerList2()
            
            self.backgroundRect = LazyTextBackground()
            self.backgroundRect.setRect( QtCore.QRectF(0, 0, self.currentDocument.width(), self.currentDocument.height()) )
            self.currentTextCanvas.scene.addItem(self.backgroundRect)
            
            if self.currentLayer.type() == 'vectorlayer':
                shapes = self.currentLayer.shapes()
                self.currentTextCanvas.fillLayer(self.currentLayer, shapes)
 
        

    def canvasAdjust(self):
        self.canvas = Krita.instance().activeWindow().activeView().canvas()
        if self.currentTextCanvas is None:
            return False
        hbar = self.scrollArea.horizontalScrollBar()
        vbar = self.scrollArea.verticalScrollBar()
        
        if self.currentTextCanvas.scene.canvasZoomLevel != self.canvas.zoomLevel():
            self.currentTextCanvas.view.resetTransform()
            self.currentTextCanvas.scene.canvasResolution = self.currentDocument.resolution()
            self.currentTextCanvas.scene.canvasBaseZoomLevel = self.currentDocument.resolution()/72
            self.currentTextCanvas.scene.canvasZoomLevel = self.canvas.zoomLevel()
            self.currentTextCanvas.scene.canvasZoomFactor = self.currentTextCanvas.scene.canvasZoomLevel/self.currentTextCanvas.scene.canvasBaseZoomLevel
            
            docwidth = hbar.maximum() - hbar.minimum() + hbar.pageStep()
            docheight = vbar.maximum() - vbar.minimum() + vbar.pageStep()
            zoomFactor = self.currentTextCanvas.scene.canvasZoomFactor

            self.currentTextCanvas.view.scale(zoomFactor,zoomFactor)
            self.currentTextCanvas.view.setSceneRect(hbar.minimum()/zoomFactor,
                                   vbar.minimum()/zoomFactor,
                                   docwidth/zoomFactor,
                                   docheight/zoomFactor)
            

            
        self.currentTextCanvas.view.horizontalScrollBar().setValue( hbar.value() )
        self.currentTextCanvas.view.verticalScrollBar().setValue( vbar.value() )
        


    def unbindScrollArea(self):
        self.scrollArea.horizontalScrollBar().valueChanged.disconnect(self.canvasAdjust)
        self.scrollArea.verticalScrollBar().valueChanged.disconnect(self.canvasAdjust)   

    def bindScrollArea(self):
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.canvasAdjust)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.canvasAdjust)
        
    def bindToolButton(self):
        if self.toolboxButtonFilterItem is None:
            qwin = Krita.instance().activeWindow().qwindow()
            toolBox = qwin.findChild(QtWidgets.QDockWidget, "ToolBox")
            textToolButton = qwin.findChild(QtWidgets.QToolButton, "SvgTextTool")
            self.toolboxButtonFilterItem = self.toolboxButtonFilter(self)
            textToolButton.installEventFilter(self.toolboxButtonFilterItem)

    def unbindToolButton(self):
        if self.toolboxButtonFilterItem is not None:
            qwin = Krita.instance().activeWindow().qwindow()
            toolBox = qwin.findChild(QtWidgets.QDockWidget, "ToolBox")
            textToolButton = qwin.findChild(QtWidgets.QToolButton, "SvgTextTool")
            textToolButton.removeEventFilter(self.toolboxButtonFilterItem)
            self.toolboxButtonFilterItem = None

    def bindLayerList2(self):
        qwin = Krita.instance().activeWindow().qwindow()
        layerBox = qwin.findChild(QtWidgets.QDockWidget, "KisLayerBox")
        layerList = layerBox.findChild(QtWidgets.QTreeView,"listLayers")
        
        layerList.selectionModel().selectionChanged.connect(self.layerChanged)
        layerList.model().sourceModel().rowsRemoved.connect(self.layerRemoved)
    
    def documentChanged(self):
        print ("DOCUMENT CHANGED!", self.currentDocument, Krita.instance().activeDocument())
        qwin = Krita.instance().activeWindow().qwindow()
        toolBox = qwin.findChild(QtWidgets.QDockWidget, "ToolBox")
        textToolButton = qwin.findChild(QtWidgets.QToolButton, "SvgTextTool")
        
        LazyTextTool.closeTextCanvas(self)
        if textToolButton.isChecked():
            LazyTextTool.openTextCanvas(self)

    def layerRemoved(self):
        if self.kritaVersion >= 5 or self.currentTextCanvas.writeItemQueue is None:
            self.layerChanged(None,None)        
    
    def layerChanged(self, selected, deselected):
        print ("ONTAB", self.onTab, self.mdi.findChild(QtWidgets.QTabBar).currentIndex() )
        if self.onTab != self.mdi.findChild(QtWidgets.QTabBar).currentIndex():
            self.documentChanged()
        
        if self.currentTextCanvas is None: return
        print ("LAYER CHANGED!", self.currentTextCanvas.writeItemQueue)
        if self.currentTextCanvas.writeItemQueue is not None:
            self.resetCurrentLayer()
            self.currentTextCanvas.finishWriteItem( self.currentTextCanvas.writeItemQueue )
            self.currentTextCanvas.writeItemQueue = None
            shapes = self.currentLayer.shapes()
            self.currentTextCanvas.fillLayer(self.currentLayer, shapes)
            return
        
        if self.currentTextCanvas.selectedAlienItem is not None:
            self.setCurrentLayer()
            self.currentTextCanvas.selectedAlienItem = None
            return
        
        if self.currentLayer.type() == 'vectorlayer' and self.currentLayer.visible() is False and self.currentTextCanvas.scene.modifyMode and self.kritaVersion < 5:
            self.currentTextCanvas.scene.modifyMode=False
            self.currentLayer.setVisible(True)
            self.currentDocument.refreshProjection()
        
        self.resetCurrentLayer()
        self.canvasAdjust()
        
        if self.currentLayer.type() == 'vectorlayer' and self.currentLayer.visible():
            shapes = self.currentLayer.shapes()
            if len(shapes) == 0:
                self.currentTextCanvas.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
                return
            elif (len(shapes) == 1 or self.kritaVersion >= 5) and shapes[0].type() == 'KoSvgTextShapeID':
                self.currentTextCanvas.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
                self.currentTextCanvas.fillLayer(self.currentLayer, shapes)
                return
        elif self.currentLayer.type() != 'vectorlayer':
             self.currentTextCanvas.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
             return
        
        self.currentTextCanvas.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        #disable temp 

    def unbindLayerList2(self):
        qwin = Krita.instance().activeWindow().qwindow()
        layerBox = qwin.findChild(QtWidgets.QDockWidget, "KisLayerBox")
        layerList = layerBox.findChild(QtWidgets.QTreeView,"listLayers")
        
        layerList.selectionModel().selectionChanged.disconnect(self.layerChanged)
        layerList.model().sourceModel().rowsRemoved.disconnect(self.layerRemoved)
    
    def bindLayerList(self):
        qwin = Krita.instance().activeWindow().qwindow()
        layerBox = qwin.findChild(QtWidgets.QDockWidget, "KisLayerBox")
        layerList = layerBox.findChild(QtWidgets.QTreeView,"listLayers")
        self.layerListFilter = self.layerListFilter(self)
        layerList.installEventFilter(self.layerListFilter)

    def unbindLayerList(self):        
        qwin = Krita.instance().activeWindow().qwindow()
        layerBox = qwin.findChild(QtWidgets.QDockWidget, "KisLayerBox")
        layerList = layerBox.findChild(QtWidgets.QTreeView,"listLayers")
        layerList.removeEventFilter(self.layerListFilter)
        


    def setup(self):
        pass
    
    def closeViewEvent(self):
        print ("CLOSE VIEW", Krita.instance().activeWindow().activeView().visible())
        self.closeTextCanvas(True)
        if Krita.instance().activeWindow().activeView().visible() == False:
            self.unbindToolButton()
        else:
            self.onTab = -1
            self.layerChanged(None,None)


    def openViewEvent(self):
        print ("OPEN VIEW")
        self.bindToolButton()
        self.onTab = -1

      

    def toggleTextTool(self, toggle=None):
        notify = Krita.instance().notifier()
        
        if self.active == True:
            notify.viewClosed.disconnect(self.closeViewEvent)
            notify.viewCreated.disconnect(self.openViewEvent)
            self.unbindToolButton()
            self.closeTextCanvas()
            self.active=False
        else:
            self.bindToolButton()
            self.active=True
            qwin = Krita.instance().activeWindow().qwindow()
            toolBox = qwin.findChild(QtWidgets.QDockWidget, "ToolBox")
            textToolButton = qwin.findChild(QtWidgets.QToolButton, "SvgTextTool")
            notify.setActive(True)
            
            notify.viewClosed.connect(self.closeViewEvent)
            notify.viewCreated.connect(self.openViewEvent)

            if textToolButton.isChecked():
                self.openTextCanvas()
                self.layerChanged(None,None)

    def createActions(self, window):
        action = window.createAction("toggleLazyTextTool", "Toggle Lazy Text Tool", "tools/scripts")
        action.setCheckable(True)
        action.triggered.connect(self.toggleTextTool)

# And add the extension to Krita's list of extensions:
app = Krita.instance()
extension = LazyTextTool(parent=app) #instantiate your class
app.addExtension(extension)
