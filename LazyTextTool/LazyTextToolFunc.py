from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os.path
import html 
import re
from xml.dom import minidom
import xml.etree.ElementTree as ET
from io import StringIO
import math
import binascii
import base64


class LazyTextUtils():
       
    ATTR2STYLE_MAP = {
            "fill":{"alias":"color","type":["color","RGBAColor","fill-opacity"]},
            "font-size":{"append":"pt"},
            "font-weight":{"round":-2},
            "font-style":{},
            "text-decoration":{},
            "font-family":{},
            "baseline-shift":{"alias":"vertical-align"},
            "letter-spacing":{},
            "font-stretch":{},
            "font-variant":{},
            "word-spacing":{},
            "font-size-adjust":{},
            "text-anchor":{"alias":"text-align","values":{ "":"left", "start":"left", "middle":"center", "end":"right" }}

    }
    
    STYLE2ATTR_MAP = {
            "color~1":{"alias":"fill","type":["color","HtmlColor"]},
            "color~2":{"alias":"fill-opacity","type":["color","Opacity"]},
            "font-size":{"replace":["pt",""]},
            "font-weight":{"round":-2},
            "font-style":{},
            "text-decoration":{},
            "font-family":{"replace":["','",","]},
            "vertical-align":{"alias":"baseline-shift"},
            "letter-spacing":{},
            "text-align":{"alias":"text-anchor","values":{ "":"start", "left":"start", "center":"middle", "right":"end" }}
    }

    @staticmethod
    def applyFormatSettings(tcursor, fmt, attr, pos=None):

        if pos is not None:
            tcursor.setPosition(pos[0])
            tcursor.setPosition(pos[1], QtGui.QTextCursor.KeepAnchor)       

        if 'letter-spacing' in attr: 
            fmt.setFontLetterSpacingType( QtGui.QFont.AbsoluteSpacing )
            fmt.setFontLetterSpacing( float(attr['letter-spacing']) )
          
            print ("MYPOS", pos[0], pos[1], fmt.fontLetterSpacing() )
        
        if 'stroke' in attr:
            outlinePen = fmt.textOutline()
            strokeColor = QtGui.QColor(attr['stroke'])
            
            
            if 'stroke-opacity' in attr:
                strokeColor.setAlphaF(float(attr['stroke-opacity'])*255)
            outlinePen.setColor( strokeColor )
            

            if attr['stroke'] == 'none':
                outlinePen.setStyle(QtCore.Qt.NoPen)
            elif 'stroke-dasharray' in attr:
                for item in LazyTextEdit.STROKE_STYLE_TYPES:
                    if item[2] == attr['stroke-dasharray']: outlinePen.setStyle(item[1])
            else:
                outlinePen.setStyle(QtCore.Qt.SolidLine)

            if 'stroke-linecap' in attr:
                for item in LazyTextEdit.STROKE_CAP_TYPES:
                    if item[0].lower() == attr['stroke-linecap'].lower(): outlinePen.setCapStyle(item[1])

            if 'stroke-linejoin' in attr:
                for item in LazyTextEdit.STROKE_JOIN_TYPES:
                    if item[0].lower() == attr['stroke-linejoin'].lower(): outlinePen.setJoinStyle(item[1])

            if 'stroke-width' in attr:
                outlinePen.setWidth(float(attr['stroke-width']))
                
            fmt.setTextOutline(outlinePen)
        

        tcursor.mergeCharFormat(fmt)
       
        '''
        outlinePen = fmt.textOutline()
        
        if outlinePen.style() == QtCore.Qt.NoPen:
            #if 'stroke' in opts: 
            el.set('stroke', 'none' )
        else:
            el.set('stroke', outlinePen.color().name() )
            el.set('stroke-opacity', outlinePen.color().alpha()/255 )
            el.set('stroke-width', outlinePen.width() )
                        
            print ( "STROKETEST", el.text, el.attrib )

            for (i, item) in enumerate(LazyTextEdit.STROKE_STYLE_TYPES):
                if i >= 2 and item[1] == outlinePen.style() : el.set('stroke-dasharray', item[2].lower() )
        
            for item in LazyTextEdit.STROKE_CAP_TYPES:
                if item[1] == outlinePen.capStyle(): el.set('stroke-linecap', item[0].lower() )
        
            for item in LazyTextEdit.STROKE_JOIN_TYPES:
                if item[1] == outlinePen.joinStyle(): el.set('stroke-linejoin', item[0].lower() )
        '''
    @staticmethod
    def applyBlockSettings(newSettings, doc):
        
        currentSettings = LazyTextUtils.loadBlockSettings(doc)
        print ("APPLY LINE SETTINGS");
        
        print ("CURRENT SETTINGS", currentSettings)
        print ("NEW SETTINGS", newSettings)
        
        blockCount = len(newSettings)-1
        for bi in range(len(newSettings)):
            block = doc.findBlockByNumber(bi)
            onFragment = 0
            
            blockFormat = None
            charFormat = None
            

            
            if 'lineheight' in newSettings[bi]:
                currentLineHeight = currentSettings[bi]['ascent']+currentSettings[bi]['descent']
                
                lineCount = len(currentSettings[bi]['lines'])
                lineScale = 0.00
                lineHeight = currentLineHeight
                

                if lineCount >= 2:
                    lineScale = float( float(newSettings[bi]['lines'][0]['lineheight']) - currentSettings[bi]['lines'][1]['ascent'] + currentSettings[bi]['lines'][0]['ascent'] ) / float(currentSettings[bi]['lines'][0]['ascent'] + currentSettings[bi]['lines'][0]['descent'])
                    print ("LS", lineScale, ( float(newSettings[bi]['lines'][0]['lineheight']), "-", currentSettings[bi]['lines'][1]['ascent'], "+", currentSettings[bi]['lines'][0]['ascent'] ), "/", (currentSettings[bi]['lines'][0]['ascent'], "+", currentSettings[bi]['lines'][0]['descent'])  )
                elif bi < blockCount:
                    print ("NS", float(newSettings[bi]['lines'][-1]['lineheight']))
                    print ("NS2", currentSettings[bi+1]['lines'][0]['ascent'])
                    lineScale = float( float(newSettings[bi]['lines'][-1]['lineheight']) - currentSettings[bi+1]['lines'][0]['ascent'] + currentSettings[bi]['lines'][-1]['ascent'] ) / float(currentSettings[bi]['lines'][-1]['ascent'] + currentSettings[bi]['lines'][-1]['descent'])
                else:
                    lineScale = 1.0
                
                #((currentBlockAbsoluteLineOffset - currLineAscent + prevLineAscent) / (prevLineAscent + prevLineDescent)) * 100.0
                
                #lineScale = ( float(newSettings[bi]['lineheight']) - currentSettings[bi+1]['lines'][0]['ascent'] + currentSettings[bi+1]['lines'][0]['descent'] ) / (currentSettings[bi]['lines'][0]['ascent'] + currentSettings[bi]['lines'][0]['descent'])

                print("BLOCKLINE", bi, newSettings[bi]['lineheight'])
                #lineScale = float(newSettings[bi]['lineheight'])/currentLineHeight
                print ("SCALE", lineScale,"HEIGHT", currentLineHeight, "LC", lineCount, "BI", bi, "LH", lineHeight)
                blockUData = block.userData()

                if not blockUData:
                    blockUData = LazyTextBlockUserData()
                    block.setUserData(blockUData)
            
                blockUData.setLineScale(lineScale)
                blockUData.setLineHeight( lineHeight )
            
                blockFormat = block.blockFormat()
                #blockFormat.setLineHeight( float(newSettings[bi]['lineheight']), QtGui.QTextBlockFormat.FixedHeight )
                #???blockFormat.setLineHeight( lineScale*100, QtGui.QTextBlockFormat.ProportionalHeight )
            
            '''
            if 'letterspacing' in newSettings[bi]:
                charFormat = block.charFormat()
                charFormat.setFontLetterSpacingType( QtGui.QFont.AbsoluteSpacing )
                charFormat.setFontLetterSpacing( float(newSettings[bi]['letterspacing']) )
                print ("LTS",newSettings[bi]['letterspacing']  )
            '''
            bcursor = QtGui.QTextCursor(block)
            pos = block.position()
            if blockFormat is not None:
                bcursor.mergeBlockFormat(blockFormat)  

            '''
            if charFormat is not None:
                
                pos = block.position()
                bcursor.setPosition(pos)
                bcursor.setPosition(pos+block.length(), QtGui.QTextCursor.KeepAnchor)
                bcursor.mergeCharFormat(charFormat)
            '''
            blockAttr = newSettings[bi]['attrib']
            charFormat = block.charFormat()
            LazyTextUtils.applyFormatSettings(bcursor, charFormat, blockAttr)
            
            textFormats = block.textFormats()
            
            #print ("TEXTFORM", textFormats[0].start, textFormats[0].length )
            print ("FRAGTEXTALL", newSettings[bi]['fragments'] )
            
            pos = [block.position(),0]
            blockLayout = block.layout()
            linePos = []
            
            for i in range(blockLayout.lineCount()):
                line = blockLayout.lineAt(i)
                linePos.append( line.textStart()+line.textLength() )
            
            print ("LINEDIFFCOUNT",blockLayout.lineCount())
            for fragment in newSettings[bi]['fragments']:
                tcursor = QtGui.QTextCursor(block)
                fmt = QtGui.QTextCharFormat()
                attr = newSettings[bi]['fragments'][onFragment]['attrib']
                textLength = len(newSettings[bi]['fragments'][onFragment]['text'])
                pos[1]=pos[0]+textLength
                
                print ("FRAGGY!", bi, linePos[0], len(linePos) )
                
                
                while pos[1] >= linePos[0] and len(linePos) > 1:
                    pos[1]+=1
                    linePos.pop(0)
                    
                
                pos[1]+=blockLayout.lineForTextPosition(pos[1]).lineNumber() - blockLayout.lineForTextPosition(pos[0]).lineNumber()
                
                LazyTextUtils.applyFormatSettings(tcursor, fmt, attr, pos)
                pos[0]=pos[1]
                
                
                onFragment+=1



    @staticmethod
    def loadDocMaxWidth(doc):
        docMaxWidthDict = { 'width':0, 'blockNum':0 }
        
        textBlock = doc.firstBlock()
        for blockNum in range(doc.blockCount()):
            #if textBlock is None: textBlock = doc.begin()
            blockLayout = textBlock.layout()
            
            #if blockLayout.maximumWidth() > docMaxWidthDict['width']:
            #    docMaxWidthDict['width']=blockLayout.maximumWidth()
            #    docMaxWidthDict['blockNum']=blockNum
            
            #if blockLayout.minimumWidth() > docMaxWidthDict['width']:
            #    docMaxWidthDict['width']=blockLayout.minimumWidth()
            #    docMaxWidthDict['blockNum']=blockNum
            currentBlockWidth = 0
            
            for li in range(blockLayout.lineCount()):
                line = blockLayout.lineAt(li)
                
                currentBlockWidth+=line.naturalTextWidth()
                
            if currentBlockWidth > docMaxWidthDict['width']:
                docMaxWidthDict['width']=currentBlockWidth
                docMaxWidthDict['blockNum']=blockNum
            
            textBlock = textBlock.next()
            
        return docMaxWidthDict

    @staticmethod
    def loadBlockSettings(doc):
        blockSettings = []
        print ("BLOCK COUNT=", doc.blockCount()  )
        bi = 0
        textBlock = doc.firstBlock()
        
        for blockNum in range(doc.blockCount()):
            #if textBlock is None: textBlock = doc.begin()
            
            blockFormat = textBlock.blockFormat()
            blockLayout = textBlock.layout()
            
            blockUData = textBlock.userData()

            if not blockUData:
                blockUData = LazyTextBlockUserData()
                textBlock.setUserData(blockUData)

            #>>print ("NBLOCK!", bi, blockFormat.alignment(), "=", textBlock.text() )
            blockSettings.append({
                'linescale': blockUData.lineScale(),
                'start':textBlock.position(),
                'ascent':0,
                'descent':0,
                'width':0,
                'alignment':blockFormat.alignment(),
                'format': QtGui.QTextCursor(textBlock).charFormat(),
                'lines':[],
                'fragments':[]
                })
            print ("total lines", blockLayout.lineCount())
            for li in range(blockLayout.lineCount()):
                line = blockLayout.lineAt(li)
                if blockSettings[bi]['ascent'] < line.ascent(): blockSettings[bi]['ascent']=line.ascent()
                if blockSettings[bi]['descent'] < line.descent(): blockSettings[bi]['descent']=line.descent()
                if blockSettings[bi]['width'] < line.naturalTextWidth(): blockSettings[bi]['width']=line.naturalTextWidth()
                blockSettings[bi]['lines'].append({
                    'width':line.naturalTextWidth(),
                    'start':line.textStart(),
                    'length':line.textLength(),
                    'ascent':line.ascent(),
                    'descent':line.descent(),
                    })
                print ("LINE", line.x(), line.y(), blockSettings[bi] )
            

            
            it = textBlock.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    
                    
                    #cursor = QtGui.QTextCursor(textBlock)
                    #cursor.setPosition(fragment.position())
                    #cursor.setPosition((fragment.position()+fragment.length()), QtGui.QTextCursor.KeepAnchor)
                    
                    blockSettings[bi]['fragments'].append({ 'text': fragment.text(), 'format': fragment.charFormat() })
                    #print("FRAGMENT", bi,  fragment.text(), fragment.charFormat().fontLetterSpacing(), fragment.charFormat().fontLetterSpacingType() ==  QtGui.QFont.AbsoluteSpacing  )
                    #blockSettings[bi]['fragments'].append({ 'text': fragment.text(), 'format': fragment.charFormat() })
                    #print("FRAGMENT2", bi,  cursor.selectedText(), cursor.charFormat().fontLetterSpacing(), cursor.charFormat().fontLetterSpacingType() == QtGui.QFont.AbsoluteSpacing  )
                it += 1    
                
            textBlock = textBlock.next()
            bi+=1

        print ("loaded block", blockSettings)    
        return blockSettings


 
    @staticmethod
    def styleToDict(style):
        styleDict = {}
        if style is not None and style != '':
            for styleDataString in re.split('^\s+|\s*;\s*',style):
                styleData = re.split('\s*:\s*',styleDataString)
                if styleData[0] != '':
                    #print ("SD", styleData)
                    styleDict[ styleData[0] ] = styleData[1]
            
        return styleDict

    @staticmethod
    def buildElement(tag, attrib):
        buildOutput = '<'+tag;
        for (key,val) in attrib.items():
            print ("KEY", key, val)
            buildOutput+=' '+key+'="'+val+'"'
        buildOutput+='>'
        return buildOutput

    @staticmethod
    def buildElement2(item):
        if isinstance(item, list):
            buildOutput = '<'+item[0];
            for (key,val) in item[1].items():
                print ("KEY", key, val)
                buildOutput+=' '+str(key)+'="'+str(val)+'"'
            buildOutput+='>'
            return buildOutput
        else:
          return item  

    @staticmethod
    def calcAlignment(width, block, onLine):
        #print ("ALIGNDATA", width, block['lines'][onLine]['width']  )
        if block['alignment'] == QtCore.Qt.AlignCenter:
            return str(width/2)
        elif block['alignment'] == QtCore.Qt.AlignRight:
            return str(width)
        else:
            return '0'


    @staticmethod
    def calcColor(colorName, returnType, opacityLevel=None):

        colorMatch = re.search(r'rgba{0,1}\((\d+?),(\d+?),(\d+?)(?:,([\d\.]+?)|)\)',colorName)
        color = None
        
        if colorMatch is None or colorMatch.group(1) is None:
            color = QtGui.QColor(colorName)
        else:
            color = QtGui.QColor(int(colorMatch.group(1)),int(colorMatch.group(2)),int(colorMatch.group(3)),
                              (255 if colorMatch.group(4) is None else int(float(colorMatch.group(4))*255) )
            )
                         
        if opacityLevel is not None:
            color.setAlpha(float(opacityLevel)*255)
        
        if returnType == 'HtmlColor':
            return color.name()
        elif returnType == 'RGBAColor':
            return 'rgba('+str(color.red())+','+str(color.green())+','+str(color.blue())+','+str(color.alpha()/255)+')'
        
        elif returnType == 'Opacity':
            return str(color.alpha()/255)
        

    @staticmethod
    def calcLineHeight(blockSettings,onBlock,onLine):
        prevLineHeight = 0 # onBlock == 0 and onLine == 0

        print ("CALCLINE", onBlock, onLine, len(blockSettings) )
        
        if onBlock >= 0 and onLine > 0:
            print ("CALCLINE2", len(blockSettings[onBlock]['lines']), blockSettings[onBlock]['lines'] )
            #prevLineHeight = (blockSettings[onBlock]['ascent']+blockSettings[onBlock]['descent']) * blockSettings[onBlock]['linescale']
            #prevLineHeight = (blockSettings[onBlock]['lines'][onLine-1]['ascent']+blockSettings[onBlock]['lines'][onLine-1]['descent']) * blockSettings[onBlock]['linescale']
            prevLineHeight = blockSettings[onBlock]['lines'][onLine]['ascent'] - blockSettings[onBlock]['lines'][onLine-1]['ascent'] + (blockSettings[onBlock]['lines'][onLine-1]['ascent'] + blockSettings[onBlock]['lines'][onLine-1]['descent']) * blockSettings[onBlock]['linescale']
            
        elif onBlock > 0 and onLine == 0:
            #prevLineHeight = (blockSettings[onBlock-1]['ascent']+blockSettings[onBlock-1]['descent']) * blockSettings[onBlock-1]['linescale']
            #prevLineHeight = (blockSettings[onBlock-1]['lines'][-1]['ascent']+blockSettings[onBlock-1]['lines'][-1]['descent']) * blockSettings[onBlock-1]['linescale']
            prevLineHeight = blockSettings[onBlock]['lines'][onLine]['ascent'] - blockSettings[onBlock-1]['lines'][-1]['ascent'] + (blockSettings[onBlock-1]['lines'][-1]['ascent'] + blockSettings[onBlock-1]['lines'][-1]['descent']) * blockSettings[onBlock-1]['linescale']

        return prevLineHeight

    @staticmethod
    def formatToHtml(el, fmt):
        
        if fmt.fontLetterSpacingType() == QtGui.QFont.AbsoluteSpacing:
            el.set('letter-spacing', fmt.fontLetterSpacing() )
                        
        outlinePen = fmt.textOutline()
        
        if outlinePen.style() == QtCore.Qt.NoPen:
            #if 'stroke' in opts: 
            el.set('stroke', 'none' )
        else:
            el.set('stroke', outlinePen.color().name() )
            el.set('stroke-opacity', outlinePen.color().alpha()/255 )
            el.set('stroke-width', outlinePen.width() )
                        
            print ( "STROKETEST", el.text, el.attrib )

            for (i, item) in enumerate(LazyTextEdit.STROKE_STYLE_TYPES):
                if i >= 2 and item[1] == outlinePen.style() : el.set('stroke-dasharray', item[2].lower() )
        
            for item in LazyTextEdit.STROKE_CAP_TYPES:
                if item[1] == outlinePen.capStyle(): el.set('stroke-linecap', item[0].lower() )
        
            for item in LazyTextEdit.STROKE_JOIN_TYPES:
                if item[1] == outlinePen.joinStyle(): el.set('stroke-linejoin', item[0].lower() )
                        
                        #for linestyle in LazyTextUtils.
                        #el.set('stroke-dasharray', outlinePen.style() )
                        
                        #stroke="#ff0000" stroke-opacity="0.219607843137255" stroke-width="1" stroke-linecap="butt" stroke-linejoin="round"
                        #stroke="#ff0000" stroke-width="1" stroke-linecap="square" stroke-linejoin="bevel"
    @staticmethod
    def htmlToSvg(htmlContent, opts):
        #etree = ET.ElementTree(ET.fromstring(htmlContent))
        etree = ET.iterparse(StringIO(htmlContent), events=("start", "end"))
        svgContent= ''
        svgContentList = []
        depthList = []
        
        tagConvert = {
            'body':{'tag':'text','type':'root'},
            'p':{'tag':'tspan','type':'block'},
            'br':None,
            'span':{'tag':'tspan','type':'mark'},
            'b':{'tag':'tspan','type':'mark', 'style':'font-weight: 700' },
            'strong':{'tag':'tspan','type':'mark', 'style':'font-weight: 700' },
            'i':{'tag':'tspan','type':'mark', 'style':'font-style: italic' },
            'em':{'tag':'tspan','type':'mark', 'style':'font-style: italic' },
            'u':{'tag':'tspan','type':'mark', 'style':'text-decoration: underline' },
            }
        
        prettyIndent = {
            'block':' ' * 4,
            'line':' ' * 8,
            'mark':' ' * 12,
            'text':' ' * 12,
            }
        
        onBlock = -1
        onLine = 0
        onFragment = 0
        
        pretty = 1
        
        
        for event,el in etree:
            if event == 'start':
                styleDict = LazyTextUtils.styleToDict(el.get('style'))
                print ( "style", styleDict, el.attrib )
                

                
                if el.tag in tagConvert and tagConvert[el.tag] is not None:
                    if el.tag == 'body':
                        svgPosX = str(LazyTextUtils.pxToPts(opts['x'], opts['resolution']))
                        svgPosY = str(LazyTextUtils.pxToPts(opts['y'], opts['resolution']) + opts['blockSettings'][0]['ascent'] )     
                        el.set('transform', 'translate('+svgPosX+','+svgPosY+')')
                        el.set('id', LazyTextUtils.nameGen(opts['unique'], opts['resolution'], opts['wrap'], opts['width'] ) )
                        #LazyTextUtils.formatToHtml(el, opts['docSettings']['format'])
                    
                    elif el.tag == 'p':
                        onBlock+=1
                        onLine=0
                        onFragment=0
                        el.set('data-type','block')
                        if 'align' not in el.attrib:
                            el.set('align', 'left')
                            
                        el.set('text-anchor', LazyTextUtils.STYLE2ATTR_MAP['text-align']['values'][el.get('align')])
                        del el.attrib['align']
                        print ("ONBLOCK", onBlock)
                        el.set('x', LazyTextUtils.calcAlignment(opts['width'],opts['blockSettings'][onBlock],onLine) )
                        el.set('dy', str(LazyTextUtils.calcLineHeight(opts['blockSettings'], onBlock, 0)))
                        LazyTextUtils.formatToHtml(el, opts['blockSettings'][onBlock]['format'])
                        
                    if 'style' in tagConvert[el.tag]:
                        el.set('style', tagConvert[el.tag]['style'] )
                    
                    print ("TAG", el.tag)

                    #if el.text is not None: print ("0FORMAT", onFragment, el.text,  opts['blockSettings'][onBlock]['fragments'][onFragment]['text'] )
                    if el.text is not None and onFragment < len(opts['blockSettings'][onBlock]['fragments']) and opts['blockSettings'][onBlock]['fragments'][onFragment]['text'].startswith(el.text):
                        print ("1FORMAT", el.text)
                        LazyTextUtils.formatToHtml(el, opts['blockSettings'][onBlock]['fragments'][onFragment]['format'])
                        
                        onFragment+=1
                    
                    if 'style' in el.attrib:
                        for attrKey, attrData in LazyTextUtils.STYLE2ATTR_MAP.items():
                            dictKey = attrKey.split('~')[0]
                            if dictKey in styleDict:
                                attrValue = (attrData['values'][styleDict[dictKey]] if 'values' in attrData.keys() else styleDict[dictKey])
                                if 'append' in attrData.keys(): attrValue += attrData['append']
                                if 'replace' in attrData.keys(): attrValue = attrValue.replace(attrData['replace'][0],attrData['replace'][1])
                                if 'round' in attrData.keys(): attrValue = str(round(float(attrValue),attrData['round']) if attrData['round'] > 0 else int(round(float(attrValue),attrData['round'])))
                                if 'type' in attrData.keys():
                                    if attrData['type'][0] == 'color':
                                        attrValue = LazyTextUtils.calcColor(attrValue,attrData['type'][1])
                                attrName = attrData['alias'] if 'alias' in attrData.keys() else attrKey
                                attrValue = ','.join(list(map(lambda x: re.sub(r"^\s*'(.*)'\s*$",r"\1", x), attrValue.split(','))))
                                el.set(attrName, attrValue)
                        del el.attrib['style']
                        
                    depthList.append({ 'el': el, 'type':tagConvert[el.tag]['type'], 'tag':tagConvert[el.tag]['tag'] })
                    svgContentList.append( [tagConvert[el.tag]['tag'], el.attrib ] )
                elif el.tag == 'br':
                    onLine+=1
                    print ("DEPTHLIST", len(depthList), onLine)
                    for i in range(len(depthList)-1,0,-1):
                        print ("DEPTHTYPE", depthList[i]['type'] )
                        if depthList[i]['type'] == 'block' or depthList[i]['type'] == 'line':
                            el.set('data-type','line')
                            el.set('x', LazyTextUtils.calcAlignment(opts['width'],opts['blockSettings'][onBlock],onLine) )
                            el.set('dy', str(LazyTextUtils.calcLineHeight(opts['blockSettings'], onBlock, onLine)))
                            if depthList[i]['type'] == 'block':
                                i+=1
                                #print ("ISERT INTO", i, depthList[i])
                                depthList.insert(i,{ 'el': el, 'type':'line', 'tag':'tspan' })
                                print ("ISERT INTO2", i, depthList)
                            else:
                                svgContentList.append( "</tspan>" )
                                
                            #svgContentList.append( buildElement('tspan', el.attrib ) )
                            
                            for i2 in range(i,len(depthList)):
                                svgContentList.append( [depthList[i2]['tag'], depthList[i2]['el'].attrib ] )
  
                            break
                        else:
                            print ("CLOSING~")
                            svgContentList.append( "</"+depthList[i]['tag']+">" )
            
                print ("%s: '%s' = %s" % (el.tag, el.text, el.tail))
                if el.text is not None and el.tag in tagConvert: svgContentList.append( el.text )
            elif event == 'end':

                    
                if el.tag in tagConvert and tagConvert[el.tag] is not None:
                    svgContentList.append( "</"+tagConvert[el.tag]['tag']+">" )
                    depthItem = depthList.pop()
                    print ("depthItem", el.tag, depthItem)
                    if el.tag == 'p' and depthItem['type'] == 'line':
                        svgContentList.append( "</"+tagConvert[el.tag]['tag']+">" )
                        depthItem = depthList.pop()

                if el.tail is not None: svgContentList.append( el.tail )

                if el.tag == 'body': break
            #    print ("end", el.tag)
        print ("OUT", "\n".join([ LazyTextUtils.buildElement2(item) for item in svgContentList ]) )
        return "".join([ LazyTextUtils.buildElement2(item) for item in svgContentList ])

    @staticmethod
    def svgToDocument(svgContent):
        htmlData = LazyTextUtils.svgToHtml2(svgContent)
        htmlData['content'] = re.sub(r'(<p[^>]*?>)[ ]*?</p>',r'\1&nbsp;</p>', htmlData['content'])
        print ("HTML2", htmlData['content'])
        doc = LazyTextUtils.htmlToDocument( htmlData['content'] )

        return [doc, htmlData['docSettings'], htmlData['blockSettings'] ]
      
    @staticmethod
    def htmlToDocument(htmlContent):
        doc = QtGui.QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultStyleSheet("baseline-shift:baseline;");
        doc.setHtml(htmlContent)

                
        return doc

    @staticmethod
    def svgToHtml2(svgContent):        
        etree = ET.iterparse(StringIO(svgContent), events=("start", "end"))
        etree = ET.iterparse(StringIO(svgContent), events=("start", "end"))

        depthList = []
        htmlContentList = ["<style>p { margin: 0px; padding: 0px }</style>"]
        blockSettings = []
        docSettings = {}
        onBlock = -1
        onLine = 0
        
        tagConvert = {
                'root':{ 'tag':"body" },
                'block':{ 'tag':"p" },
                'line':{ 'tag':"span" },
                'mark':{ 'tag':"span" }
        }

        elementList = []
        
        for event,el in etree:
            elementList.append({ 'event': event, 'el': el, 'type':'unknown' })
        
        for i in range(len(elementList)):
            el=elementList[i]['el']
            if elementList[i]['event'] == 'start':
                styleDict = LazyTextUtils.styleToDict(el.get('style'))
                
                for attrKey, attrData in LazyTextUtils.ATTR2STYLE_MAP.items():
                    if attrKey in el.attrib:
                        attrValue = (attrData['values'][el.get(attrKey)] if 'values' in attrData.keys() else el.get(attrKey))
                        if 'append' in attrData.keys(): attrValue += attrData['append']
                        if 'replace' in attrData.keys(): attrValue = attrValue.replace(attrData['replace'][0],attrData['replace'][1])
                        if 'round' in attrData.keys(): attrValue = str(round(float(attrValue),attrData['round']) if attrData['round'] > 0 else int(round(float(attrValue),attrData['round'])))
                        if 'type' in attrData.keys():
                            if attrData['type'][0] == 'color':
                                attrValue = LazyTextUtils.calcColor(attrValue,attrData['type'][1], (el.get(attrData['type'][2]) if attrData['type'][2] in el.attrib else None))
                        attrName = attrData['alias'] if 'alias' in attrData.keys() else attrKey
                        styleDict[attrName]=attrValue
                
               
                attr = { 
                    'style': ' '.join([
                        '%s: %s;' % (
                            key, 
                            "'"+ "','".join(list(map(lambda x: x.replace("'", r"\'"), re.split(r'\s*,\s*', value))))+"'" if ' ' in value else value 
                            ) for (key, value) in styleDict.items()
                    ]) 
                }
                
                if el.tag == 'text':
                    elementType = "root"
                    docSettings['version']=0
                    
                    if 'id' in el.attrib:
                        print ("ID FOUND!")
                        docData = re.search(r'^t(\d)_(\d+)_(\d)([\d\.]+)_(.+)$', el.get('id'))
                        if docData is not None:
                            docSettings['version']=int(docData.group(1))
                            docSettings['resolution']=int(docData.group(2))
                            docSettings['wrapmode']=int(docData.group(3))
                            docSettings['boundarywidth']=float(docData.group(4))
                            docSettings['crc32']=docData.group(5)

                elif el.tag == 'tspan':
                    elementType = "mark"
                    if 'text-anchor' in el.attrib:
                        elementType = "block"

                    elif 'dy' in el.attrib or 'x' in el.attrib:
                        if len(depthList) == 1:
                            elementType = "block"
                        else:
                            elementType = "line"
                            
                            
                    elif len(depthList) == 1 and ('dy' in elementList[i+1]['el'].attrib
                                                  or 'x' in elementList[i+1]['el'].attrib
                                                  ):
                        elementType = "block"

                print ("ELM", elementList[i]['el'].attrib )
                if elementType in tagConvert:
                    if elementType == "block":
                        blockSettings.append({ 'lines':[{}], 'fragments':[], 'attrib':{}, 'lineheight':0 })
                        onBlock+=1
                        onLine=0
                        blockSettings[onBlock]['attrib'] = attr
                       
                        if 'letter-spacing' in el.attrib:
                            blockSettings[onBlock]['letterspacing']=el.get('letter-spacing')
                        
                        if 'text-anchor' in el.attrib:
                            blockSettings[onBlock]['align']=el.get('text-anchor')
                        
                    elif elementType == "line" and elementList[i-1]['type'] != 'block':
                        htmlContentList.append("<br />")
                        blockSettings[onBlock]['lines'].append({})
                        onLine+=1
                        
  
                    if 'dy' in el.attrib:
                        bi = onBlock if onLine >= 1 else onBlock-1
                        print ("LINEINFO", onBlock, onLine, "BI", bi, el.get('dy') )
                        if bi >= 0:
                            if float(blockSettings[bi]['lineheight']) < float(el.get('dy')): blockSettings[bi]['lineheight']=el.get('dy')
                            blockSettings[bi]['lines'][onLine-1]['lineheight']=el.get('dy')

                    elementList[i]['type']=elementType
                    attr['data-type']=elementType
                    depthList.append({ 'el': el, 'type':elementType, 'tag':tagConvert[elementType]['tag'] })
                    htmlContentList.append( [tagConvert[elementType]['tag'], attr] )
                    
                
                    if el.text is not None:
                        if onBlock == -1:
                            blockSettings.append({ 'lines':[{}], 'fragments':[], 'attrib':{}, 'lineheight':0 })
                            onBlock+=1
                            onLine=0
                        blockSettings[onBlock]['fragments'].append({ 'text': el.text, 'attrib': el.attrib  })
                        htmlContentList.append( el.text )                      
            elif elementList[i]['event'] == 'end':
                depthItem = depthList.pop()
                print ("CLOSEME", el.tail, depthItem, tagConvert[depthItem['type']]['tag'] )
                htmlContentList.append( "</"+tagConvert[depthItem['type']]['tag']+">" )
                if el.tail is not None:
                    blockSettings[onBlock]['fragments'].append({ 'text': el.tail, 'attrib': depthList[len(depthList)-1]['el'].attrib  })
                    htmlContentList.append( el.tail )
                
        print ("OUT", "\n".join([ LazyTextUtils.buildElement2(item) for item in htmlContentList ]), docSettings, blockSettings )
        return { 'content': "".join([ LazyTextUtils.buildElement2(item) for item in htmlContentList ]), 'docSettings': docSettings , 'blockSettings': blockSettings}


    @staticmethod
    def svgToHtml(svgContent):
        etree = ET.iterparse(StringIO(svgContent), events=("start", "end"))

        depthList = []
        htmlContentList = ["<style>p { margin: 0px; padding: 0px }</style>"]
        blockSettings = []
        docSettings = {}
        onBlock = -1
        onLine = 0
        
        tagConvert = {
                'root':{ 'tag':"body" },
                'block':{ 'tag':"p" },
                'line':{ 'tag':"span" },
                'mark':{ 'tag':"span" }
        }
        
        for event,el in etree:
            if event == 'start':
                styleDict = LazyTextUtils.styleToDict(el.get('style'))
                
                for attrKey, attrData in LazyTextUtils.ATTR2STYLE_MAP.items():
                    if attrKey in el.attrib:
                        attrValue = (attrData['values'][el.get(attrKey)] if 'values' in attrData.keys() else el.get(attrKey))
                        if 'append' in attrData.keys(): attrValue += attrData['append']
                        if 'replace' in attrData.keys(): attrValue = attrValue.replace(attrData['replace'][0],attrData['replace'][1])
                        if 'round' in attrData.keys(): attrValue = str(round(float(attrValue),attrData['round']) if attrData['round'] > 0 else int(round(float(attrValue),attrData['round'])))
                        if 'type' in attrData.keys():
                            if attrData['type'][0] == 'color':
                                attrValue = LazyTextUtils.calcColor(attrValue,attrData['type'][1], (el.get(attrData['type'][2]) if attrData['type'][2] in el.attrib else None))
                        attrName = attrData['alias'] if 'alias' in attrData.keys() else attrKey
                        styleDict[attrName]=attrValue
                
               
                attr = { 
                    'style': ' '.join([
                        '%s: %s;' % (
                            key, 
                            "'"+value.replace("'", r"\'")+"'" if ' ' in value else value 
                            ) for (key, value) in styleDict.items()
                    ]) 
                }
                
                if el.tag == 'text':
                    elementType = "root"
                    docSettings['version']=0
                    
                    if 'id' in el.attrib:
                        print ("ID FOUND!")
                        docData = re.search(r'^t(\d)_(\d+)_(\d)([\d\.]+)_(.+)$', el.get('id'))
                        if docData is not None:
                            docSettings['version']=int(docData.group(1))
                            docSettings['resolution']=int(docData.group(2))
                            docSettings['wrapmode']=int(docData.group(3))
                            docSettings['boundarywidth']=float(docData.group(4))
                            docSettings['crc32']=docData.group(5)
                    
                elif el.tag == 'tspan':
                    elementType = "mark"
                    if 'text-anchor' in el.attrib:
                        elementType = "block"
                        
                    elif 'dy' in el.attrib or 'x' in el.attrib:
                        if len(depthList) == 1:
                            elementType = "block"
                        else:
                            elementType = "line"
                            print("FOUND LINE", len(depthList), onBlock, len(blockSettings), blockSettings  )
                            #print ("FOUND LINE!!!", el.text, ('lineheight' in blockSettings[onBlock]) )
                            if blockSettings[onBlock]['firstline']:
                                onLine+=1
                            else:
                                blockSettings[onBlock]['firstline']=True
                    elif len(depthList) == 1 and (len(el.attrib) == 0 or onBlock == -1):
                        elementType = "block"

                if elementType in tagConvert:
                    if elementType == "block":
                        blockSettings.append({ 'lines':[{}], 'fragments':[], 'attrib':{}, 'firstline':False })
                        onBlock+=1
                        onLine=0
                        blockSettings[onBlock]['attrib'] = attr
                        if 'dy' in el.attrib or 'x' in el.attrib:
                            blockSettings[onBlock]['firstline'] = True
                        
                        if 'letter-spacing' in el.attrib:
                            blockSettings[onBlock]['letterspacing']=el.get('letter-spacing')
                        
                    
                    if 'text-anchor' in el.attrib:
                        blockSettings[onBlock]['align']=el.get('text-anchor')
                        
                    if elementType == "line" and onLine >= 1:
                        htmlContentList.append("<br />")
                        blockSettings[onBlock]['lines'].append({  })                        
                        
                        
                    if 'dy' in el.attrib:
                        bi = onBlock if onLine >= 1 else onBlock-1
                        blockSettings[bi]['lineheight']=el.get('dy')
                        blockSettings[bi]['lines'][onLine]['lineheight']=el.get('dy')
                    
                    

                    
                    attr['data-type']=elementType
                    depthList.append({ 'el': el, 'type':elementType, 'tag':tagConvert[elementType]['tag'] })
                    htmlContentList.append( [tagConvert[elementType]['tag'], attr] )
                    
                
                    if el.text is not None:
                        if onBlock == -1:
                            blockSettings.append({ 'lines':[{}], 'fragments':[], 'attrib':{}, 'firstline':False })
                            onBlock+=1
                            onLine=0
                        blockSettings[onBlock]['fragments'].append({ 'text': el.text, 'attrib': el.attrib  })
                        htmlContentList.append( el.text )   
            elif event == 'end':
             
                
                depthItem = depthList.pop()
                print ("CLOSEME", el.tail, depthItem, tagConvert[depthItem['type']]['tag'] )
                htmlContentList.append( "</"+tagConvert[depthItem['type']]['tag']+">" )
                if el.tail is not None:
                    blockSettings[onBlock]['fragments'].append({ 'text': el.tail, 'attrib': depthList[len(depthList)-1]['el'].attrib  })
                    htmlContentList.append( el.tail )
                
        print ("OUT", "\n".join([ LazyTextUtils.buildElement2(item) for item in htmlContentList ]), docSettings, blockSettings )
        return { 'content': "".join([ LazyTextUtils.buildElement2(item) for item in htmlContentList ]), 'docSettings': docSettings , 'blockSettings': blockSettings}

    @staticmethod
    def pxToPts(pixels, dpi):
        return (pixels*72)/dpi
    
    @staticmethod
    def ptsToPx(points, dpi):
        return (points/72)*dpi
        #return points*(72/dpi)
        
    @staticmethod  
    def nameGen(uniqueString,docRes, wrapMode, boundryWidth):
        n = binascii.crc32(str.encode(uniqueString))
        byte_length = (n.bit_length() + 7) // 8
        encodedString = base64.urlsafe_b64encode(n.to_bytes(byte_length, 'big')).decode('utf-8').rstrip('=')
        return 't1_' + str(docRes) + '_' + str(wrapMode) + str(boundryWidth) + '_' + encodedString
    

    def svgDocument(svgContent, docWidth, docHeight, docRes):
        svgWidth = str(LazyTextUtils.ptsToPx(docWidth, docRes))
        svgHeight = str(LazyTextUtils.ptsToPx(docHeight, docRes))
        return '''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<!-- Created using Krita: https://krita.org -->
<svg xmlns="http://www.w3.org/2000/svg" 
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:krita="http://krita.org/namespaces/svg/krita"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    width="''' + svgWidth + '''pt"
    height="''' + svgHeight + '''pt"
    viewBox="0 0 ''' + svgWidth + ' ' + svgHeight + '''">
<defs/>''' + svgContent + "</svg>"


    @staticmethod
    def distance(a,b):
        if b < a:
            return math.sqrt((a - b)**2)*-1
        else:
            return math.sqrt((a - b)**2)


class LazyTextHelper(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LazyTextHelper, self).__init__(parent)
        uic.loadUi(os.path.dirname(os.path.realpath(__file__)) + '/LazyTextToolHelper.ui', self)
        self.hide()
        #hbox=QtWidgets.QHBoxLayout(self)
        #hbox.addWidget(self.mainWidget)

        self.blockMode = False
        self.target = None
        self.currentColor = None
        self.currentStrokeColor = None
        self.firstRun = False
        self.defaultSettings = { 'font': QtGui.QFont() }
        
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        #self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.WindowDoesNotAcceptFocus)
        #self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint | QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowDoesNotAcceptFocus)
        
        
        self.opacityEffect = QtWidgets.QGraphicsOpacityEffect(self);
        self.opacityEffect.setOpacity(0.5)
        self.setGraphicsEffect(self.opacityEffect);
        
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.textWrapComboBox.addItem('Typewriter')
        self.textWrapComboBox.addItem('TextWrap')
        
        for item in LazyTextEdit.STROKE_STYLE_TYPES:
            self.strokeStyleComboBox.addItem(item[0],item[1])

        for item in LazyTextEdit.STROKE_CAP_TYPES:
            self.strokeCapsComboBox.addItem(item[0],item[1])

        for item in LazyTextEdit.STROKE_JOIN_TYPES:
            self.strokeJoinsComboBox.addItem(item[0],item[1])
        
        self.boldButton.clicked.connect(self.textBold)
        self.italicsButton.clicked.connect(self.textItalic)
        self.underlineButton.clicked.connect(self.textUnderline)

        
        self.colorButton.clicked.connect(self.openColorDialog)
        
        self.fontComboBox.currentFontChanged.connect(self.setCurrentFont)
        self.fontSizeDSpinBox.valueChanged.connect(self.setCurrentFontSize)
        
        self.alignLeftButton.clicked.connect(self.setAlignLeft)
        self.alignCenterButton.clicked.connect(self.setAlignCenter)
        self.alignRightButton.clicked.connect(self.setAlignRight)
        
        self.lineSpacingDSpinBox.valueChanged.connect(self.setLineSpacing)
        self.letterSpacingDSpinBox.valueChanged.connect(self.setLetterSpacing)

        self.strikeButton.clicked.connect(self.textStrike)

        self.subButton.clicked.connect(self.textSubscript)
        self.supButton.clicked.connect(self.textSuperscript)
        
      
        
        self.textWrapComboBox.currentIndexChanged.connect(self.textWrapMode)
        
        
        self.strokeClearButton.clicked.connect(self.strokeClear)

        self.strokeThicknessDSpinBox.valueChanged.connect(self.setStrokeThickness)

        self.strokeStyleComboBox.currentIndexChanged.connect(self.setStrokeStyle)
        self.strokeCapsComboBox.currentIndexChanged.connect(self.setStrokeCaps)
        self.strokeJoinsComboBox.currentIndexChanged.connect(self.setStrokeJoins)
        
        self.strokeColorButton.clicked.connect(self.openStrokeColorDialog)

        
        
        
        self.boldMenu = QtWidgets.QMenu()
        

        
        self.fontWeightActions = []
        
        for i in range(9):
            self.fontWeightActions.append( self.boldMenu.addAction("%d00 - %s" % (i+1, LazyTextEdit.BOLD_TYPES[i][0]) ) )
            font = QtGui.QFont()
            font.setWeight(LazyTextEdit.BOLD_TYPES[i][1])
            self.fontWeightActions[i].setFont(font)
            self.fontWeightActions[i].setCheckable(True)
            self.fontWeightActions[i].setData(LazyTextEdit.BOLD_TYPES[i][1])
            self.fontWeightActions[i].triggered.connect(self.fontWeightAction)
        
        self.boldButton.setMenu(self.boldMenu)
    
    def setDialogDefaults(self):
        if self.firstRun == False:
            return;
        self.setCurrentFont(self.defaultSettings['font'])
        self.setCurrentFontSize(self.defaultSettings['font'].pointSizeF())
     
        
        
    
    def showFor(self, target, useDefaults = True):
        if self.target is not None:
            self.target.cursorPositionChanged.disconnect(self.updateFormatButtons)
        
        self.target = target
        self.target.cursorPositionChanged.connect(self.updateFormatButtons)
        if useDefaults == True: 
            self.setDialogDefaults()
        self.updateFormatButtons(self.target.textCursor())
        self.firstRun = True
        self.show()
        self.target.setFocus()

    def hideDialog(self):
        self.target = None
        self.hide()

    def enterEvent(self, event):
        super(LazyTextHelper, self).enterEvent(event)
        self.opacityEffect.setOpacity(1)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.ArrowCursor)
        
    def leaveEvent(self, event):
        super(LazyTextHelper, self).leaveEvent(event)
        self.opacityEffect.setOpacity(0.5)
        QtWidgets.QApplication.restoreOverrideCursor()
    
    def setAlignLeft(self):
        self.setAlignment(QtCore.Qt.AlignLeft)
    def setAlignCenter(self):
        self.setAlignment(QtCore.Qt.AlignCenter)
    def setAlignRight(self):
        self.setAlignment(QtCore.Qt.AlignRight)

    def setAlignment(self,alignment):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextBlockFormat()
        fmt.setAlignment(alignment) 
        tcursor.mergeBlockFormat(fmt)
        self.updateFormatButtons(tcursor)

    
    def updateFormatButtons(self, tcursor):
        
        charFormat = tcursor.charFormat()
        blockFormat = tcursor.blockFormat()
        font = charFormat.font()

        
        self.blockMode = True
        self.fontComboBox.setCurrentFont(font)
        self.fontSizeDSpinBox.setValue(font.pointSizeF())
        self.currentColor = charFormat.foreground().color()
        self.colorButton.setStyleSheet('background-color: %s; color: %s' % (
            self.currentColor.name(),
            '#fff' if self.currentColor.value() < 90 else '#000'
            ) 
        )
        self.colorButton.setText(str(self.currentColor.alpha()))
        
        self.italicsButton.setChecked(font.italic())
        self.underlineButton.setChecked(font.underline())
        self.boldButton.setChecked(font.bold())
        
        self.alignLeftButton.setChecked( blockFormat.alignment() == QtCore.Qt.AlignLeft)
        self.alignCenterButton.setChecked( blockFormat.alignment() == QtCore.Qt.AlignCenter)
        self.alignRightButton.setChecked( blockFormat.alignment() == QtCore.Qt.AlignRight)
        
        block = tcursor.block()
        blockUData = block.userData()

        if not blockUData:
            blockUData = LazyTextBlockUserData()
            block.setUserData(blockUData)

        self.lineSpacingDSpinBox.setValue( blockUData.lineScale()*100 )
        #???self.lineSpacingDSpinBox.setValue( blockUData.lineScale()*100 if blockFormat.lineHeightType() == QtGui.QTextBlockFormat.ProportionalHeight else 100 )
        #self.lineSpacingDSpinBox.setValue( blockUData.lineScale()*100 if blockFormat.lineHeightType() == QtGui.QTextBlockFormat.FixedHeight else 100 )
        self.letterSpacingDSpinBox.setValue( charFormat.fontLetterSpacing() if charFormat.fontLetterSpacingType() == QtGui.QFont.AbsoluteSpacing else 0 )
        
        self.strikeButton.setChecked(font.strikeOut())
        #self.textWrapButton.setChecked( self.target.parentItem().textWrapMode == LazyTextObject.TEXTWRAP_MODE )
        self.textWrapComboBox.setCurrentIndex( self.target.parentItem().textWrapMode )
        
        for action in self.fontWeightActions:
            action.setChecked( charFormat.fontWeight() == action.data() )
        
        outlinePen = charFormat.textOutline()
        
        print ("OUTSTYLE",outlinePen, outlinePen.style(), outlinePen.width() )
        
        self.currentStrokeColor = outlinePen.color()
        self.strokeColorButton.setStyleSheet('background-color: %s; color: %s' % (
            self.currentStrokeColor.name(),
            '#fff' if self.currentStrokeColor.value() < 90 else '#000'
            ) 
        )
        self.strokeColorButton.setText(str(self.currentStrokeColor.alpha()))
        
        self.strokeStyleComboBox.setCurrentIndex( outlinePen.style() )
        self.strokeThicknessDSpinBox.setValue( outlinePen.width() )
        
        self.strokeCapsComboBox.setCurrentIndex( self.strokeCapsComboBox.findData(outlinePen.capStyle()) )
        self.strokeJoinsComboBox.setCurrentIndex( self.strokeJoinsComboBox.findData(outlinePen.joinStyle()) )
        
        self.blockMode = False


    def getMaxLineHeight(self,block):
        blockLayout = block.layout()
        lineHeight = 0
        for li in range(blockLayout.lineCount()):
            line = blockLayout.lineAt(li)
            if lineHeight < line.ascent() + line.descent():
                lineHeight = line.ascent() + line.descent()
        return lineHeight    

    def selectedBlocks(self):
        doc = self.target.document()
        tcursor = self.getCursor()
        startBlock = doc.findBlock(tcursor.selectionStart()).blockNumber() 
        endBlock = doc.findBlock(tcursor.selectionEnd()).blockNumber()
        blockList = []
        
        for block in range(startBlock, endBlock+1):
            blockList.append( doc.findBlockByNumber(block) )
            
        return blockList
        
        
    def openColorDialog(self, color):
        colorDlg = QtWidgets.QColorDialog(self)
        colorDlg.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        if self.currentColor:
            colorDlg.setCurrentColor(QtGui.QColor(self.currentColor))

        if colorDlg.exec_():
            self.setColor(colorDlg.currentColor().name(),colorDlg.currentColor().alpha())
            self.colorButton.setStyleSheet('background-color: %s; color: %s' % (
                self.currentColor.name(),
                '#fff' if self.currentColor.value() < 90 else '#000'
                ) 
            )
            self.colorButton.setText(str(self.currentColor.alpha()))



    def setColor(self,color,alpha):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        self.currentColor = QtGui.QColor(color)
        self.currentColor.setAlpha(alpha)
        fmt.setForeground(self.currentColor)
        tcursor.mergeCharFormat(fmt)

    def setCurrentFontSize(self,fontSize):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontPointSize(fontSize)
        tcursor.mergeCharFormat(fmt)
        self.defaultSettings['font'].setPointSizeF(fontSize)
        if self.target.toPlainText() == '':
            font = self.target.font()
            font.setPointSizeF(fontSize)
            self.target.setFont(font)
        
        self.setLineSpacing()
        
        '''
        lineHeight = 0
        selectedBlocks = self.selectedBlocks()
        
        for block in selectedBlocks:
            blockMaxHeight = self.getMaxLineHeight(block)
            if lineHeight < blockMaxHeight:
                lineHeight = blockMaxHeight
        fmt2 = QtGui.QTextBlockFormat()    
        fmt2.setLineHeight(lineHeight, QtGui.QTextBlockFormat.FixedHeight )
        #fmt2.setLineHeight(LazyTextUtils.ptsToPx(lineHeight, self.target.scene().canvasResolution ), QtGui.QTextBlockFormat.FixedHeight )
        tcursor.mergeBlockFormat(fmt2)
        
        for block in selectedBlocks:
            data = block.userData()

            if not data:
                data = LazyTextBlockUserData()
                block.setUserData(data)
            
            data.setLineHeight(lineHeight)
            
            #self.target.blockBaseHeight[str(block.blockNumber())] = lineHeight
        '''

    def setLineSpacing(self, lineScale=None):
        if self.blockMode: return
        tcursor = self.getCursor()
        
        if lineScale is not None:
            lineScale/=100;
        selectedBlocks = self.selectedBlocks()
        
        for block in selectedBlocks:
            blockMaxHeight = self.getMaxLineHeight(block)
            blockUData = block.userData()

            if not blockUData:
                blockUData = LazyTextBlockUserData()
                block.setUserData(blockUData)

            #baseLineHeight = blockMaxHeight / blockUData.lineScale()
            
            #print ("MAX", blockMaxHeight, "BASELINE", baseLineHeight, "OLDSCALE", blockUData.lineScale(), "NEWSCALE", lineScale )
            
            if lineScale is not None:
                blockUData.setLineScale(lineScale)
            blockUData.setLineHeight(blockMaxHeight)
            
            #calcLineHeight(blockSettings,onBlock,onLine)
            
            #if block.blockNumber() > 0:
            fmt = block.blockFormat()
            print ("BLOCK HEIGHT", blockMaxHeight)
            blockHeightOffset = fmt.lineHeight()
            print ("LINEH", blockHeightOffset )
            
            #fmt.setLineHeight( blockMaxHeight * (blockUData.lineScale()+0.4), QtGui.QTextBlockFormat.FixedHeight )
            #block.layout().lineAt(0).setPosition(QtCore.QPointF(50,50))
            print ("FIRST LINE POS", block.layout().lineAt(0).position() )
            #QTextLine::setPosition(const QPointF &pos)
            #???fmt.setLineHeight( blockUData.lineScale()*100 , QtGui.QTextBlockFormat.ProportionalHeight )
           
            #fmt.setLineHeight( lineSpacing, QtGui.QTextBlockFormat.ProportionalHeight )
            bcursor = QtGui.QTextCursor(block)
            bcursor.mergeBlockFormat(fmt)   

    def setLetterSpacing(self,fontSpacing):
        if self.blockMode: return
        tcursor = self.getCursor()
        #fmt = QtGui.QTextCharFormat()
        fmt = tcursor.charFormat()
        fmt.setFontLetterSpacingType( QtGui.QFont.AbsoluteSpacing )
        fmt.setFontLetterSpacing( fontSpacing )
        
        tcursor.mergeCharFormat(fmt)

        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockCharFormat.setFontLetterSpacingType( QtGui.QFont.AbsoluteSpacing )
                blockCharFormat.setFontLetterSpacing( fontSpacing )
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)


    def strokeClear(self):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = QtGui.QPen()
        outlinePen.setStyle(QtCore.Qt.NoPen)
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)
        
        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockCharFormat.setTextOutline(outlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)

    def setStrokeThickness(self,strokeSize):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = fmt.textOutline()
        outlinePen.setWidth(strokeSize);
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)

        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockOutlinePen = blockCharFormat.textOutline()
                blockOutlinePen.setWidth(strokeSize);
                blockCharFormat.setTextOutline(blockOutlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)

    def setStrokeStyle(self,strokeStyleID):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = fmt.textOutline()
        strokeStyle = LazyTextEdit.STROKE_STYLE_TYPES[strokeStyleID][1]
        outlinePen.setStyle(strokeStyle);
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)
        
        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockOutlinePen = blockCharFormat.textOutline()
                blockOutlinePen.setStyle(strokeStyle);
                blockCharFormat.setTextOutline(blockOutlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)

    def setStrokeCaps(self,strokeCapID):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = fmt.textOutline()
        strokeCap = LazyTextEdit.STROKE_CAP_TYPES[strokeCapID][1]
        outlinePen.setCapStyle(strokeCap)
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)
        
        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockOutlinePen = blockCharFormat.textOutline()
                blockOutlinePen.setCapStyle(strokeCap)
                blockCharFormat.setTextOutline(blockOutlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)


    def setStrokeJoins(self,strokeJoinID):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = fmt.textOutline()
        strokeJoin = LazyTextEdit.STROKE_JOIN_TYPES[strokeJoinID][1]
        outlinePen.setJoinStyle(strokeJoin)
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)
        
        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockOutlinePen = blockCharFormat.textOutline()
                blockOutlinePen.setJoinStyle(strokeJoin)
                blockCharFormat.setTextOutline(blockOutlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)


    def openStrokeColorDialog(self, color):
        colorDlg = QtWidgets.QColorDialog(self)
        colorDlg.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        if self.currentStrokeColor:
            colorDlg.setCurrentColor(QtGui.QColor(self.currentStrokeColor))

        if colorDlg.exec_():
            self.setStrokeColor(colorDlg.currentColor().name(),colorDlg.currentColor().alpha())
            self.strokeColorButton.setStyleSheet('background-color: %s; color: %s' % (
                self.currentStrokeColor.name(),
                '#fff' if self.currentStrokeColor.value() < 90 else '#000'
                ) 
            )
            self.strokeColorButton.setText(str(self.currentStrokeColor.alpha()))

    def setStrokeColor(self, strokeColor, strokeAlpha):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        outlinePen = fmt.textOutline()
        self.currentStrokeColor = QtGui.QColor(strokeColor)
        self.currentStrokeColor.setAlpha(strokeAlpha)
        outlinePen.setColor(self.currentStrokeColor)
        fmt.setTextOutline(outlinePen)
        tcursor.mergeCharFormat(fmt)
        
        for block in self.selectedBlocks():
            if tcursor.selectionStart() <= block.position() and tcursor.selectionEnd() >= block.position()+block.length()-1:
                blockCharFormat = block.charFormat()
                blockOutlinePen = blockCharFormat.textOutline()
                blockOutlinePen.setColor(self.currentStrokeColor)
                blockCharFormat.setTextOutline(blockOutlinePen)
                QtGui.QTextCursor(block).setCharFormat(blockCharFormat)
        
        
    def setCurrentFont(self,font):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontFamily(font.family())
        tcursor.mergeCharFormat(fmt)
        self.defaultSettings['font'].setFamily(font.family())
        if self.target.toPlainText() == '':
            currentFont = self.target.font()
            currentFont.setFamily(font.family())
            self.target.setFont(currentFont)

    def fontWeightAction(self,toggle):
        self.setFontWeight(self.sender().data())
        for action in self.fontWeightActions:
            action.setChecked( self.sender().data() == action.data() )

    def setFontWeight(self,fontWeight):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        print ( tcursor.charFormat().fontWeight(), "!=", fontWeight )
        if (tcursor.charFormat().fontWeight() != fontWeight):
            fmt.setFontWeight( fontWeight )
        else:
            fmt.setFontWeight( QtGui.QFont.Normal )
        tcursor.mergeCharFormat(fmt)
    
    def textWrapMode(self,textMode):
        self.target.parentItem().textWrapMode = textMode
            
    
    def textBold(self,toggle):
        if self.blockMode: return
        print ("ADDED BOLD!") 
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        if (tcursor.charFormat().font().bold() is False):
            fmt.setFontWeight( QtGui.QFont.Bold )
        else:
            fmt.setFontWeight( QtGui.QFont.Normal )
        tcursor.mergeCharFormat(fmt)

    def textItalic(self,toggle):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        if (tcursor.charFormat().font().italic() is False):
            fmt.setFontItalic( QtGui.QFont.StyleItalic )
        else:
            fmt.setFontItalic( QtGui.QFont.StyleNormal )
        tcursor.mergeCharFormat(fmt);
    
    def textUnderline(self,toggle):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontUnderline( not tcursor.charFormat().font().underline() )
        tcursor.mergeCharFormat(fmt)

    def textStrike(self,toggle):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut( not tcursor.charFormat().font().strikeOut() )
        tcursor.mergeCharFormat(fmt)

    def textSubscript(self,toggle):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        align = fmt.verticalAlignment()
        if (align == QtGui.QTextCharFormat.AlignNormal):
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        tcursor.setCharFormat(fmt)

    def textSuperscript(self,toggle):
        if self.blockMode: return
        tcursor = self.getCursor()
        fmt = tcursor.charFormat()
        align = fmt.verticalAlignment()
        if (align == QtGui.QTextCharFormat.AlignNormal):
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        tcursor.setCharFormat(fmt)

    def getCursor(self):
        tcursor = self.target.textCursor()
        if (not tcursor.hasSelection()):
            tcursor.select(QtGui.QTextCursor.WordUnderCursor);
        return tcursor

class LazyTextBlockUserData(QtGui.QTextBlockUserData):
    def __init__(self):
        super(LazyTextBlockUserData, self).__init__()
        self.lineHeightData = 0
        self.lineScaleData = 1

    def lineHeight(self):
        return self.lineHeightData
 
    def setLineHeight(self, lineHeight):
        self.lineHeightData = lineHeight

    def lineScale(self):
        return self.lineScaleData
 
    def setLineScale(self, lineHeight):
        self.lineScaleData = lineHeight

class LazyTextTempBox(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        super(LazyTextTempBox, self).__init__(parent)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable);
        #self.objectType = "LazyTextTempBox"


class LazyTextEdit(QtWidgets.QGraphicsTextItem):
    cursorPositionChanged = QtCore.pyqtSignal(['QTextCursor'])

    BOLD_TYPES = [
            ['Thin',QtGui.QFont.Thin],
            ['Extra Light',QtGui.QFont.ExtraLight],
            ['Light',QtGui.QFont.Light],
            ['Normal',QtGui.QFont.Normal],
            ['Medium',QtGui.QFont.Medium],
            ['Demi Bold',QtGui.QFont.DemiBold],
            ['Bold',QtGui.QFont.Bold],
            ['Extra Bold',QtGui.QFont.ExtraBold],
            ['Black',QtGui.QFont.Black],
    ]
    
    STROKE_STYLE_TYPES = [
        ['None', QtCore.Qt.NoPen ],
        ['Solid', QtCore.Qt.SolidLine ],
        ['Dash', QtCore.Qt.DashLine, '4,2' ],
        ['Dot', QtCore.Qt.DotLine, '1,2' ],
        ['DashDot', QtCore.Qt.DashDotLine, '4,2,1,2' ],
        ['DashDotDot', QtCore.Qt.DashDotDotLine, '4,2,1,2,1,2' ]
    ]
    
    STROKE_CAP_TYPES = [
        ['Square', QtCore.Qt.SquareCap ],
        ['Flat', QtCore.Qt.FlatCap ],
        ['Round', QtCore.Qt.RoundCap ],
    ]

    STROKE_JOIN_TYPES = [
        ['Bevel', QtCore.Qt.BevelJoin ],
        ['Miter', QtCore.Qt.MiterJoin  ],
        ['Round', QtCore.Qt.RoundJoin ],
    ]
    
    def __init__(self, text, parent=None):
        super(LazyTextEdit, self).__init__(parent)
        #self.objectType = "LazyTextEdit"
        self.text = text
        self.setPlainText(text)
        self.isPressed = 0
        self.cursorPosition = 0
        self.currentHeight = 0
        
        self.defaultFont = QtGui.QFont()
        self.defaultFont.setPointSize(10)
        self.defaultFontMetrics = QtGui.QFontMetricsF(self.defaultFont)
        self.setFont(self.defaultFont)
        self.setDefaultTextColor(QtCore.Qt.black)
        
        self.document().setDocumentMargin(0)
        self.document().setDefaultStyleSheet("baseline-shift:baseline;");
        
        self.blockBaseHeight = {}
        
        self.enableEditing()
        #self.setFlag(QGraphicsItem.ItemIsMovable)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable )
        
        #self.setTextInteractionFlags(QtCore.Qt.TextEditable);

    def disableEditing(self):
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self.clearFocus()
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemStacksBehindParent, 1 )
        print ("DISABLE EDITING!")

    def enableEditing(self):
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        print ("ENABLE EDITING!")



    def focusOutEvent(self, event):
        #self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        super(LazyTextEdit, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        super(LazyTextEdit, self).keyPressEvent(event)
        cursor = self.textCursor()
        cpos = cursor.position()

        if self.cursorPosition != cpos:
            self.cursorPositionChanged.emit(cursor)
            #???self.parentItem().resizeFromTextItem()
        
        self.cursorPosition = cpos
        
        
    def mousePressEvent(self, event):
        self.isPressed = 1
        print ("CLICK EVENT",event.pos())

        super(LazyTextEdit, self).mousePressEvent(event)
        #p = self.document().documentLayout().hitTest(event.pos(), QtCore.Qt.FuzzyHit)
        
        
        #cursor.setPosition(p)
        

    def mouseDoubleClickEvent(self, event):
        #if self.textInteractionFlags() == Qt.NoTextInteraction:
        #    self.setTextInteractionFlags(Qt.TextEditorInteraction)
        print ("DBLCLICK EVENT")
        p = self.document().documentLayout().hitTest(event.pos(), QtCore.Qt.FuzzyHit)
        #cursor = self.textCursor();
        #cursor.setPosition(p);
        #self.setTextCursor(cursor);
        
        super(LazyTextEdit, self).mouseDoubleClickEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.isPressed = 0
        cursor = self.textCursor()
        cpos = cursor.position()
        if self.cursorPosition != cpos:
            self.cursorPositionChanged.emit(cursor)
            
        
        self.cursorPosition = cpos
        super(LazyTextEdit, self).mouseReleaseEvent(event)
        
    def boundingRect(self):
        return super(LazyTextEdit, self).boundingRect()
        #return super(LazyTextEdit, self).parent().boundingRect();
       
#    def paint(self,painter,option,widget):
#        painter.setPen(QtGui.QPen(QtCore.Qt.blue, 2, QtCore.Qt.SolidLine))
#        painter.drawRect(self.boundingRect())

#        super().paint(painter, option, widget)


    def paint(self,painter,option,widget):
        #self.document().firstBlock().layout().lineAt(0).setPosition( QtCore.QPointF(0, 0 ) )
        #super(LazyTextEdit, self).paint(painter,option,widget)
        cursorPos = self.textCursor().position()
        cursorPoint1 = QtCore.QPointF(-1,-1)
        cursorPoint2 = QtCore.QPointF(-1,-1)
        cursorBlockPos = -1

        iblock = self.document().begin()
        #blockHeight = 0;
        #linespace = self.textCursor().blockFormat().lineHeight()
        
        
        lastHeight = 0
        lastScale = 1
        cursorPosH = 0
        totalPosH = 0
        
        blockCount = 0
        lineCount = []
   
        while iblock != self.document().end():
            textPosH = 0
            blockCount += 1
            
            

            textLayout = iblock.layout()
            if textLayout == None:
                print ("BREAK!")
                break
            
        
            blockUData = iblock.userData()

            if not blockUData:
                blockUData = LazyTextBlockUserData()
                iblock.setUserData(blockUData)

            if blockUData.lineHeight() == 0 and blockUData.lineScale() == 1:
                if blockCount == 1 and lastHeight == 0:
                    print ("FIRST BLOCK!")
                    fm = painter.fontMetrics()
                    blockUData.setLineHeight(fm.height())
                elif blockCount > 1 and lastHeight > 0:
                    print ("NEW BLOCK!")
                    blockUData.setLineHeight(lastHeight)
                    blockUData.setLineScale(lastScale)
                
            if iblock.contains(cursorPos):
                cursorBlockPos = cursorPos - iblock.position()
                
            lineCount.append(textLayout.lineCount())
            
            for i in range(textLayout.lineCount()):
                line = textLayout.lineAt(i)
                
                
                #glyphs = line.glyphRuns()
                
                #line.draw( painter, QtCore.QPointF(0, blockHeight ) );
                line.setPosition( QtCore.QPointF(0, textPosH ) )
                
                if cursorBlockPos > -1 and line.textStart() <= cursorBlockPos and cursorBlockPos <= line.textStart()+line.textLength():
                    cursorPosH += textPosH
                    cursorXPos = line.cursorToX( cursorBlockPos )
                    cursorPoint1 = QtCore.QPointF( cursorXPos[0]+0.5 , cursorPosH+0.5 )
                    cursorPoint2 = QtCore.QPointF( cursorXPos[0]+0.5 , cursorPosH + blockUData.lineHeight() - 0.5 )
                    cursorBlockPos = -1
                    
                    
                textPosH += blockUData.lineHeight() * blockUData.lineScale()
                lastHeight = blockUData.lineHeight()
                lastScale = blockUData.lineScale()
                #print ("TEXTH", blockUData.lineHeight(),blockUData.lineScale(),  textPosH)


            totalPosH += textPosH
            cursorPosH += textPosH
            iblock = iblock.next()
            

        option.exposedRect.setHeight( LazyTextUtils.ptsToPx( totalPosH+lastHeight, self.scene().canvasResolution ) )

        if self.currentHeight != option.exposedRect.height():
            print ("ADJUSTH!!!", blockCount, lineCount, option.exposedRect.height())
            self.currentHeight = option.exposedRect.height()
            self.parentItem().resizeFromTextItem()
                

                
            
            
            
        cursorBlock = self.document().findBlock( self.textCursor().position() )
        cursorLayout = cursorBlock.layout()

            
        if self.hasFocus() and self.scene().currentMode == LazyTextScene.EDIT_MODE and cursorPoint1.x() > -1:
            pen = QtGui.QPen(QtCore.Qt.black);
            pen.setWidth(1);
            painter.setPen(pen);

                
            painter.drawLine(cursorPoint1, cursorPoint2 );
                
        super(LazyTextEdit, self).paint(painter,option,widget)



class LazyTextHandle(QtWidgets.QGraphicsRectItem):
    MOVE = 1
    ROTATE = 2
    RESIZE = 3
    RESCALE = 4
    CURSORS_LIST = {
            MOVE : QtCore.Qt.OpenHandCursor, 
            ROTATE : QtCore.Qt.CrossCursor, 
            RESIZE : QtCore.Qt.SizeFDiagCursor,
            RESCALE : QtCore.Qt.CrossCursor
    }

    def __init__(self, handleType, parent=None):
        super(QtWidgets.QGraphicsRectItem, self).__init__(parent)
        #self.objectType = "LazyTextHandle"
        self.handleType = handleType
        self.posX = self.rect().x()
        self.posY = self.rect().y()
        self.setAcceptHoverEvents(True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)

    def mousePressEvent(self, event):
        scene = self.scene()
        if scene.selectedObject is not self.parentItem() or scene.currentMode != LazyTextScene.EDIT_MODE: return
        print ("PRESS HANDLE!")
        self.posX = event.scenePos().x()
        self.posY = event.scenePos().y()
        parentItem = self.parentItem()
        parentItem.textRectRatio = [ parentItem.textItem.boundingRect().width()/parentItem.rect().width(), parentItem.textItem.boundingRect().height()/parentItem.rect().height() ]
        scene.selectedObject = self;
        scene.setCurrentMode(LazyTextScene.ADJUST_MODE)
        super(LazyTextHandle, self).mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        #print ( "LOCHAND", self.sceneBoundingRect().x(),event.scenePos().x(),self.sceneBoundingRect().y(),event.scenePos().y()  );

        super(LazyTextHandle, self).mouseMoveEvent(event)

    def hoverLeaveEvent(self, event):
        super(LazyTextHandle, self).hoverLeaveEvent(event)
        QtWidgets.QApplication.restoreOverrideCursor()

    def hoverEnterEvent(self, event):
        super(LazyTextHandle, self).hoverEnterEvent(event)
        scene = self.scene()
        
        if scene.selectedObject is self.parentItem() and (scene.currentMode == LazyTextScene.ADJUST_MODE or scene.currentMode == LazyTextScene.EDIT_MODE):
            QtWidgets.QApplication.setOverrideCursor(self.CURSORS_LIST[self.handleType]);
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
        
    def paint(self,painter,option,widget):
        scene = self.scene()
        
        color=QtCore.Qt.black
        
        if scene.selectedObject is self.parentItem() and (scene.currentMode == LazyTextScene.ADJUST_MODE or scene.currentMode == LazyTextScene.EDIT_MODE):
            color=QtCore.Qt.blue
        
        painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.SolidLine))
        painter.drawRect(self.boundingRect())

        super().paint(painter, option, widget)

class LazyTextObject(QtWidgets.QGraphicsRectItem):
    TYPEWRITER_MODE = 0
    TEXTWRAP_MODE = 1
    
    def __init__(self, parent=None):
        super(QtWidgets.QGraphicsRectItem, self).__init__(parent)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable);
        #self.objectType = "LazyTextObject"
        self.textItem = None
        #self.setBrush(QtCore.Qt.red)
        self.startSelectPos = 0
        self.scaleTextObject = QtWidgets.QGraphicsScale()
        self.rotateTextObject = QtWidgets.QGraphicsRotation()
        self.rotateObject = QtWidgets.QGraphicsRotation()
        self.textRectRatio = [0,0]
        self.textWrapMode = self.TYPEWRITER_MODE



    def resizeFromTextItem(self):
        objectRect = self.rect()
        textRect = self.textItem.boundingRect()
        
        adjustRect = False
        

        
        if self.textWrapMode == self.TYPEWRITER_MODE:
            maxDocWidth = LazyTextUtils.loadDocMaxWidth(self.textItem.document())
            textWidth = LazyTextUtils.ptsToPx(maxDocWidth['width']*1.1, self.scene().canvasResolution )
            print ("NEW TEXT WIDTH",objectRect.width(), textWidth, maxDocWidth['width'] )
            #textWidth = LazyTextUtils.ptsToPx( textRect.width(), self.scene().canvasResolution )
            if objectRect.width() < textWidth:
                objectRect.setWidth(textWidth)
                self.textItem.setTextWidth(maxDocWidth['width']*1.1)
                adjustRect = True

        #???textHeight = LazyTextUtils.ptsToPx( textRect.height(), self.scene().canvasResolution )
        textHeight = self.textItem.currentHeight
        if objectRect.height() < textHeight:
            objectRect.setHeight(textHeight)
            adjustRect = True
        
        print("RECTH", objectRect.height(),textRect.height(), LazyTextUtils.ptsToPx( textRect.height(), self.scene().canvasResolution ) )
        if adjustRect is True:
            self.setRect(objectRect)
            self.adjustHandles()
        
        
               

    def adjustHandles(self):
        if hasattr(self, 'moveHandle'):
            r = self.rect()
            self.moveHandle.setRect(r.topLeft().x()-10,r.topLeft().y()-10,10,10)
            self.resizeHandle.setRect(r.topRight().x(),r.topRight().y()-10,10,10)
            #>>self.resizeHandle.setRect(r.bottomRight().x(),r.bottomRight().y(),10,10)
            #>>self.rotateHandle.setRect(r.bottomLeft().x()-10,r.bottomLeft().y(),10,10)
            #>>>self.rescaleHandle.setRect(r.topRight().x(),r.topRight().y()-10,10,10)
            self.moveHandle.update(self.moveHandle.rect())
            self.resizeHandle.update(self.resizeHandle.rect())
            
    
    
    def setHtml(self, htmlContent):
        self.textItem.setHtml(htmlContent)

    def setDocument(self, doc):
        self.textItem.setDocument(doc)

    def finalizeObject(self, content = None, r = None):
        
        if content is None:
            print (self.rect())
            r = self.rect()
            if (r.width() < 100):
                r.setWidth(100)
            if (r.height() < 50):
                r.setHeight(50)


        self.textItem = LazyTextEdit("",self)
        
        if content is not None:
            if isinstance(content[0], QtGui.QTextDocument):
                self.setDocument(content[0])
            else:
                self.setHtml(content[0])

            if 'wrapmode' in content[1]: self.textWrapMode = content[1]['wrapmode']
            LazyTextUtils.applyBlockSettings(content[2], self.textItem.document())
            

            '''
            font = self.textItem.font()
            fontMetrics = QtGui.QFontMetricsF(font)
            print ("FONT", font, fontMetrics.ascent() )
            ascent = LazyTextUtils.ptsToPx(fontMetrics.ascent()*-1, self.scene().canvasResolution )
            print ("FONT2", ascent )
            print ("ORG R", r)
            r = r.adjusted( 0, ascent, 0, ascent )
            '''
            print ("ORG R", r)
            firstLine = self.textItem.document().firstBlock().layout().lineAt(0)
            adjustLine = LazyTextUtils.ptsToPx(firstLine.ascent() , self.scene().canvasResolution)
            
            textWidth=None
            print ("DOSETT", content[1])
            if 'boundarywidth' in content[1]:
                textWidth=LazyTextUtils.ptsToPx( content[1]['boundarywidth'], content[1]['resolution'] )
            else:
                maxDocWidth = LazyTextUtils.loadDocMaxWidth(self.textItem.document())
                textWidth = LazyTextUtils.ptsToPx(maxDocWidth['width'], self.scene().canvasResolution )
            
            r.setWidth(textWidth)
            
            r = r.adjusted( 0, -adjustLine, 0, -adjustLine )
            #self.resizeFromTextItem()
            
            print ("FIXED R", r)
            


        '''
        self.textItem.document().setPageSize(
            QtCore.QSizeF( 
                LazyTextUtils.pxToPts(r.width(), self.scene().canvasResolution), 
                LazyTextUtils.pxToPts(r.height(), self.scene().canvasResolution) 
            )
        );
        '''
        #if self.textMode != self.TYPEWRITER_MODE:
        self.textItem.document().setTextWidth(
                LazyTextUtils.pxToPts(r.width(), self.scene().canvasResolution)
            )
        
        if content is not None:
            r.setHeight( LazyTextUtils.ptsToPx( self.textItem.boundingRect().height(), self.scene().canvasResolution  ) )

        print ("NHEIGHT", LazyTextUtils.ptsToPx( self.textItem.boundingRect().height(), self.scene().canvasResolution  ), r.height() )
        print ("width()", LazyTextUtils.pxToPts(r.width(), self.scene().canvasResolution))
        
        self.setRect(r)
        
       
        #self._current_text_item.setHtml("Testing")
        
        self.moveHandle = LazyTextHandle(LazyTextHandle.MOVE,self)
        self.resizeHandle = LazyTextHandle(LazyTextHandle.RESIZE,self)
        #>>self.rotateHandle = LazyTextHandle(LazyTextHandle.ROTATE,self)
        #>>self.rescaleHandle = LazyTextHandle(LazyTextHandle.RESCALE,self)
        self.adjustHandles()


        self.scaleTextObject.setXScale( self.scene().canvasBaseZoomLevel )
        self.scaleTextObject.setYScale( self.scene().canvasBaseZoomLevel )

        self.setTransformations([self.rotateObject])
        self.textItem.setTransformations([self.rotateTextObject, self.scaleTextObject])
        self.textRectRatio = [ self.textItem.boundingRect().width()/r.width(), self.textItem.boundingRect().height()/r.height() ]
        
        ##self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        
        
        #self.textItem.setFlags(QtCore.Qt.ItemSendsGeometryChanges) #maybe?
        self.setAcceptHoverEvents(1)

        print (r.x(), r.y(), r.width(), r.height())


        self.textItem.setPos(r.topLeft())

            

    def focusInEvent(self, event):
        print ("FOCUS EVENT!")
        
        super(LazyTextObject, self).focusInEvent(event)
        #self.textItem.setFocus()


    def mousePressEvent(self, event):
        print ("MOUSY!")
        if self is not self.scene().selectedObject: return
        print ("MOUSY2!")
            
        self.textItem.setFocus()
        #coords = QtCore.QPointF(abs(self.rect().x())-abs(event.scenePos().x()), abs(self.rect().y())-abs(event.scenePos().y()) )
        #coords = QtCore.QPointF(event.scenePos().x(), event.scenePos().y() )
        #coords = QtCore.QPointF( LazyTextUtils.distance(self.sceneBoundingRect().x(), event.scenePos().x()), LazyTextUtils.distance(self.sceneBoundingRect().y(),event.scenePos().y()) )

        coords = QtCore.QPointF( 
            LazyTextUtils.pxToPts( LazyTextUtils.distance(self.sceneBoundingRect().x(), event.scenePos().x()), self.scene().canvasResolution), 
            LazyTextUtils.pxToPts( LazyTextUtils.distance(self.sceneBoundingRect().y(),event.scenePos().y()), self.scene().canvasResolution)
        )

        self.startSelectPos = self.textItem.document().documentLayout().hitTest(coords, QtCore.Qt.FuzzyHit)
        print ("START SELECT", coords, self.startSelectPos)
        super(LazyTextObject, self).mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.startSelectPos = 0
        super(LazyTextObject, self).mouseReleaseEvent(event)

        
    def mouseMoveEvent(self, event):
        if self.textItem.isPressed == 0 and self.scene().currentMode == LazyTextScene.EDIT_MODE:
            coords = QtCore.QPointF( 
               LazyTextUtils.pxToPts( LazyTextUtils.distance(self.sceneBoundingRect().x(), event.scenePos().x()) , 200), 
               LazyTextUtils.pxToPts( LazyTextUtils.distance(self.sceneBoundingRect().y(),event.scenePos().y()), 200)
            )
            coords2 = QtCore.QPointF(16, 16)
            #print ("LOC2", coords.x(), coords.y(), coords2 )
            #print ( "LOC", self.sceneBoundingRect().x(),event.scenePos().x(),self.sceneBoundingRect().y(),event.scenePos().y()  );
            p = self.textItem.document().documentLayout().hitTest(coords, QtCore.Qt.FuzzyHit)
            #print ("MPoint", p, self.startSelectPos)
            cursor = self.textItem.textCursor()
            cursor.setPosition(self.startSelectPos)
            cursor.setPosition(p, QtGui.QTextCursor.KeepAnchor)
            self.textItem.setTextCursor(cursor);
        super(LazyTextObject, self).mouseMoveEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        super(LazyTextObject, self).mouseDoubleClickEvent(event)
        self.textItem.setFocus()


    def hoverEnterEvent(self, event):
        super(LazyTextObject, self).hoverEnterEvent(event)
        scene = self.scene()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.IBeamCursor)

    def hoverLeaveEvent(self, event):
        super(LazyTextObject, self).hoverLeaveEvent(event)
        scene = self.scene()
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.setOverrideCursor(scene.CURSORS_LIST.get(scene.currentMode))

    def paint(self,painter,option,widget):
        scene = self.scene()
        color = QtCore.Qt.black
        if scene.selectedObject is self.parentItem() and (scene.currentMode == LazyTextScene.ADJUST_MODE or scene.currentMode == LazyTextScene.EDIT_MODE):
            color=QtCore.Qt.blue
            
        painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.SolidLine))
        painter.drawRect(self.boundingRect())
        super().paint(painter, option, widget)       

class LazyTextView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(LazyTextView, self).__init__(parent)
        self.setStyleSheet("background: rgba(90,0,0,0%)")
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        
    def wheelEvent(self, event):
        self.parent().viewWheelEvent(event)
        print ("View Wheel")
        
    def enterEvent(self, event):
        super(LazyTextView, self).enterEvent(event)
        scene = self.scene()
        QtWidgets.QApplication.setOverrideCursor(scene.CURSORS_LIST.get(scene.currentMode))
        
    def leaveEvent(self, event):
        super(LazyTextView, self).leaveEvent(event)
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.restoreOverrideCursor()

class LazyTextBackground(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        super(QtWidgets.QGraphicsRectItem, self).__init__(parent)
        self.setFlags( QtWidgets.QGraphicsItem.ItemStacksBehindParent )
        #self.setAcceptedMouseButtons(0)
        
        
class LazyTextScene(QtWidgets.QGraphicsScene):
    INIT_MODE = 0
    DRAW_MODE = 1
    EDIT_MODE = 2
    ADJUST_MODE = 3
    WORK_MODE = 4
    CURSORS_LIST = {
            INIT_MODE : QtCore.Qt.IBeamCursor, 
            DRAW_MODE : QtCore.Qt.CrossCursor, 
            EDIT_MODE : QtGui.QCursor(QtGui.QIcon(os.path.dirname(os.path.realpath(__file__)) + '/commit_cursor.svg').pixmap(
                QtCore.QSize(32,32) if QtWidgets.QApplication.primaryScreen().size().width() <= 3000 else QtCore.QSize(64,64)  
                )),
            ADJUST_MODE : QtCore.Qt.CrossCursor,
            WORK_MODE : QtCore.Qt.CrossCursor
    }
    
    def __init__(self, parent=None):
        super(LazyTextScene, self).__init__(parent)
        self.drawStartPos = QtCore.QPointF()
        self.drawTextObject = None
        self.selectedObject = None
        self.lastSelectedObject = None
        self.canvasZoomLevel = 0
        self.canvasResolution = 0
        self.modifyMode = False
        self.setCurrentMode(self.INIT_MODE)
        
    def cleanup(self):
        self.drawTextObject = None
        self.selectedObject = None
        self.lastSelectedObject = None
        self.setCurrentMode(self.INIT_MODE)
        
        for graphicsItem in self.items():
            if not isinstance(graphicsItem,LazyTextBackground): self.removeItem(graphicsItem)
        
    def setCurrentMode(self, mode):
        self.currentMode = mode
        
        if mode == self.INIT_MODE and self.lastSelectedObject is not None and self.lastSelectedObject.textItem is not None:
            print ("LAST SELECT", self.lastSelectedObject)
            self.lastSelectedObject.textItem.disableEditing()
            self.lastSelectedObject.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable,1)
            self.selectedObject = None
        elif mode == self.EDIT_MODE and self.selectedObject is not None and isinstance(self.selectedObject, LazyTextObject) and self.selectedObject.textItem is not None:
            self.selectedObject.textItem.enableEditing()
            self.selectedObject.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable,0)
            self.selectedObject.adjustHandles()
        print ("MODE", mode, self.CURSORS_LIST.get(mode))
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.setOverrideCursor(self.CURSORS_LIST.get(mode))

    def wheelEvent(self, event):
        self.parent().sceneWheelEvent(event)
        event.accept()
        print ("Scene Wheel")



    def mouseDoubleClickEvent(self, event):
        print ("SDOUBLE")
        if self.currentMode == self.WORK_MODE or self.currentMode == self.EDIT_MODE: return
        if self.selectedObject is not None:
            self.selectedObject.textItem.setOpacity(1)
            self.setCurrentMode(self.EDIT_MODE)
            self.modifyMode = True
            print ("EDITING ITEM MODIFY", self.selectedObject)
            self.parent().editItem(self.selectedObject)
            #QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.IBeamCursor);
         
        super(LazyTextScene, self).mouseDoubleClickEvent(event)
        #>>super(LazyTextScene, self).mousePressEvent(event)

    def mousePressEvent(self, event):
        super(LazyTextScene, self).mousePressEvent(event)
        if self.currentMode == self.WORK_MODE or self.currentMode == self.ADJUST_MODE: return
        
        onItem = self.itemAt(event.scenePos(), QtGui.QTransform())
        if isinstance(onItem,LazyTextBackground): onItem = None
        
        
        if self.currentMode == self.EDIT_MODE and event.button() == QtCore.Qt.RightButton:
            print ("ON ITEM", onItem)
            if onItem is not None and (onItem is self.selectedObject or onItem.parentItem() is self.selectedObject): return
            print ("CANCEL ITEM", onItem, self.selectedObject)
            self.parent().cancelItem()
            self.setCurrentMode(self.INIT_MODE)
            return
        
        self.lastSelectedObject = self.selectedObject;
        self.selectedObject = onItem
        #items = self.items(event.scenePos())
        #for item in items:
        #    if isinstance(item,LazyTextObject):
        #        self.selectedObject = item

        

        
        print ("SSINGLE", type(self.selectedObject), self.selectedObject)
        if self.selectedObject is None:
            if self.currentMode == self.EDIT_MODE:
                print ("WRITE ITEM!")
                self.setCurrentMode(self.WORK_MODE)
                self.parent().writeItem(self.lastSelectedObject)
                self.setCurrentMode(self.INIT_MODE)
                return
            else:
                
                selectedAlienItem = self.parent().selectAlienItemAt(event.scenePos())
                
                if selectedAlienItem is None or isinstance(selectedAlienItem, LazyTextBackground):
                    print ("START DRAW!", self.currentMode)
                    self.setCurrentMode(self.DRAW_MODE)
                    self.modifyMode = False
                    self.drawTextObject = LazyTextObject()

                    self.addItem(self.drawTextObject)
                    self.drawStartPos = event.scenePos()
                    r = QtCore.QRectF(self.drawStartPos, self.drawStartPos)
                    self.drawTextObject.setRect(r)
                else:
                    print ("GET ALIEN OBJECTS!", selectedAlienItem, type(selectedAlienItem['item']), selectedAlienItem['item'] )
                    self.setCurrentMode(self.WORK_MODE)
                    selectedAlienItem['item'].textItem.setFocus()
                    self.selectedObject = selectedAlienItem['item']
                    #>>CHECK THIS>>self.setCurrentMode(self.EDIT_MODE)
                    self.setCurrentMode(self.INIT_MODE)
                    


        elif isinstance(self.selectedObject, LazyTextEdit):
            self.selectedObject = self.selectedObject.parentItem()
        #elif self.selectedObject.objectType == "LazyTextTempBox":
        #    self.drawTextObject = LazyTextObject()
        #    self.addItem(self.drawTextObject)
        #    self.drawTextObject.setRect(self.selectedObject.tempRectData)
        #    self.drawTextObject.finalizeObject(self.selectedObject.tempSvgData)
        
        if isinstance(self.selectedObject, LazyTextObject) and self.lastSelectedObject is not None and self.lastSelectedObject is not self.selectedObject:
            if self.currentMode == self.EDIT_MODE:
                print ("WRITE ITEM2!")
                self.setCurrentMode(self.WORK_MODE)
                self.parent().writeItem(self.lastSelectedObject)
                self.setCurrentMode(self.INIT_MODE)

        

    def mouseMoveEvent(self, event):
        #print ("MOVY!", self.currentMode, isinstance(self.selectedObject, LazyTextHandle))
        if self.drawTextObject is not None:
            r = QtCore.QRectF(self.drawStartPos, event.scenePos()).normalized()
            self.drawTextObject.setRect(r)
        elif self.currentMode == self.ADJUST_MODE and isinstance(self.selectedObject, LazyTextHandle):
            parentItem = self.selectedObject.parentItem()
            posDiffX = LazyTextUtils.distance(self.selectedObject.posX, event.scenePos().x())
            posDiffY = LazyTextUtils.distance(self.selectedObject.posY, event.scenePos().y())
            
            if self.selectedObject.handleType == LazyTextHandle.MOVE:
        
                parentItem.setRect( parentItem.rect().adjusted( posDiffX, posDiffY, posDiffX, posDiffY )  )
                parentItem.textItem.setPos( parentItem.rect().x(),parentItem.rect().y() )
                parentItem.adjustHandles()

                self.selectedObject.posX = event.scenePos().x()
                self.selectedObject.posY = event.scenePos().y()
            elif self.selectedObject.handleType == LazyTextHandle.RESIZE:
                parentItem.textWrapMode = LazyTextObject.TEXTWRAP_MODE
                objectRect = parentItem.rect().adjusted(0, 0, posDiffX, 0)
                parentItem.setRect(objectRect)
                parentItem.textItem.setPos(objectRect.x(), objectRect.y())
                parentItem.textItem.setTextWidth(
                    LazyTextUtils.pxToPts(objectRect.width(), self.canvasResolution)
                    )
                
                doc = parentItem.textItem.document()
                #tcursor=parentItem.textItem.textCursor()
                
                dcursor = doc.find("\u2028")
                if dcursor.hasSelection():
                    dcursor.removeSelectedText()
                
                
                parentItem.adjustHandles()

                self.selectedObject.posX = event.scenePos().x()
                self.selectedObject.posY = event.scenePos().y()
            elif self.selectedObject.handleType == LazyTextHandle.RESCALE:

                parentItem.setRect( self.selectedObject.parentItem().rect().adjusted( posDiffX*-1, posDiffY, posDiffX, posDiffY*-1 )  )

                newTextRectRatio = [ parentItem.textItem.boundingRect().width()/parentItem.rect().width(), parentItem.textItem.boundingRect().height()/parentItem.rect().height() ]

                parentItem.adjustHandles()
                
                parentItem.scaleTextObject.setXScale(parentItem.textRectRatio[0]/newTextRectRatio[0])
                parentItem.scaleTextObject.setYScale(parentItem.textRectRatio[1]/newTextRectRatio[1])
                
                self.selectedObject.parentItem().textItem.setPos( self.selectedObject.parentItem().rect().x(), self.selectedObject.parentItem().rect().y() )

                self.selectedObject.posX = event.scenePos().x()
                self.selectedObject.posY = event.scenePos().y()
                
            elif self.selectedObject.handleType == LazyTextHandle.ROTATE:
   
                parentItem.rotateObject.setOrigin( QtGui.QVector3D(parentItem.boundingRect().center()) )
        
                #print ( "ORIGIN", parentItem.rotateObject.origin(), parentItem.rotateTextObject.origin()  )
        
                parentItem.rotateObject.setAngle((posDiffX+posDiffY)*-1)
                #self.selectedObject.parentItem().textItem.setPos( self.selectedObject.parentItem().rect().x(), self.selectedObject.parentItem().rect().y() )
                #self.selectedObject.parentItem().adjustHandles()

                #self.selectedObject.posX = event.scenePos().x()
                #self.selectedObject.posY = event.scenePos().y()


        super(LazyTextScene, self).mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if self.drawTextObject is not None:
            self.drawTextObject.textWrapMode = LazyTextObject.TEXTWRAP_MODE
            self.drawTextObject.finalizeObject()
            self.drawTextObject.textItem.setFocus()
            print ("FINALIZE AFTER DRAW", self.drawTextObject)
            self.selectedObject = self.drawTextObject
            self.setCurrentMode(self.EDIT_MODE)
            self.drawTextObject = None
            self.parent().editItem(self.selectedObject)
            
            print ("SELECTED AFTER DRAW", self.selectedObject)
        elif self.currentMode == self.ADJUST_MODE and isinstance(self.selectedObject, LazyTextHandle):
            self.selectedObject = self.selectedObject.parentItem()
            self.setCurrentMode(self.EDIT_MODE)

        super(LazyTextScene, self).mouseReleaseEvent(event)



