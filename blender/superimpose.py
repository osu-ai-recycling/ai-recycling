from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

jpeg_img = Image.open("conveyor.jpg")  # Replace with the path to your JPEG image
png_img = Image.open("../output4.png")    # Replace with the path to your PNG image

border_size = 20

# Create a mask for the edges
mask = Image.new("L", png_img.size, 0)
draw = ImageDraw.Draw(mask)
draw.rectangle((0, 0, png_img.width, border_size), fill=255)
draw.rectangle((0, 0, border_size, png_img.height), fill=255)
draw.rectangle((0, png_img.height - border_size, png_img.width, png_img.height), fill=255)
draw.rectangle((png_img.width - border_size, 0, png_img.width, png_img.height), fill=255)

blurred_mask = mask.filter(ImageFilter.GaussianBlur(radius=border_size))

enhancer = ImageEnhance.Brightness(png_img)
lightened_img = enhancer.enhance(1.2)  
lightened_img.paste(png_img, (0, 0), blurred_mask)

png_img = png_img.resize(jpeg_img.size)

blurred_png_img = png_img.filter(ImageFilter.GaussianBlur(radius=2))  # Adjust the radius for blur intensity
jpeg_img.paste(blurred_png_img, (0, 0), blurred_png_img)

jpeg_img.save("superimpose.jpg")  