<:comment:>A paged listing of all image files in the current
directory, with thumbnails that link to the original image, and the
image name.  The arguments "x" and "y" can be used to specify the
dimensions of the bounding box in which the thumbnails must fit;
page_num is the current page number, and items_per_page is just
that.<:/comment:>

<:args x=`(int, 150)` 
       y=`(int, 250)` 
       page_num=`(int, 0)` 
       items_per_page=`(int, 6)`:>
<:datacomp naillist comp/list_thumbnails.dcmp 
           dirpath=`CONNECTION.uri` 
           x=`x` 
           y=`y` 
           cache=yes:>
<:datacomp pagelist comp/pager.pydcmp 
           page_num=`page_num` 
           items_per_page=`items_per_page` 
           cnt=`len(naillist)`:>
<:if `pagelist[0]>1`:>
  <:set pagetitle `" (Page %d)" % (1+page_num)`:>
<:else:>
  <:set pagetitle "":>
<:/if:>
<:import os:><:set title `'Image Listing for %s%s' % (os.path.dirname(CONNECTION.uri), pagetitle)`:>
<html><head><title><:val `title` html:></title><body>
<H2><:val `title` html:></H2>
<table width="100%"><tr><td width="200"></td><td>
<table><:for `naillist[pagelist[1]:pagelist[1]+items_per_page]` rec:>
<tr>
  <td><:url `rec[1]` text=`os.path.basename(rec[1])`:></td>
  <td><a href=<:val `rec[1]`:>><:val `rec[0]`:></a></td>
</tr>
<:/for:></table></td></tr></table>
<:if `pagelist[0]>1`:>
<P align='center'> go to page: <:for `range(pagelist[0])` numb:><:if `numb!=page_num`:>
  <:url `CONNECTION.uri` queryargs=`{'x': x, 
                                     'y' : y, 
                                     'page_num' : numb, 
                                     'items_per_page' : items_per_page }`
    text=`1+numb`:> <:else:> <:val `1+numb`:> <:/if:>&nbsp;<:/for:></P>
<:/if:>
</body></html>
