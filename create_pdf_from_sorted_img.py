# import dependencies
import re, pytesseract, cv2, os, shutil, logging, sys
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from datetime import datetime
from PIL import Image

def create_logging():
    
    """
    Enable logging to console
    ---------------------------
    This function is used to create
    and configure the logging for the
    console to show log messages.
    """
    
    # set logging configuration
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    return logger

def get_img_from_pdf(images_directory , input_pdf_path, poppler_path):
    
    """
    Get the Images from a PDF file
    ---------------------------
    This method extracts all the
    images from a PDF file and 
    stores it to a directory.

    Parameters
    ----------
    images_directory : path
        It is the path of images
        folder.
    input_pdf_path : path
        It is the path of the input
        PDF file.
    poppler_path : path
        It is the path of Poppler
        to process PDF files.
    """
    
    # Use pdf2image to extract images from the PDF file
    images = convert_from_path(input_pdf_path, poppler_path = poppler_path)

    # iterate through the extracted images from PDF
    for idx, image in enumerate(images):
        
        # Save each image to the directory
        filename = os.path.join(images_directory, f"trip_image_{idx+1}.jpg")
        image.save(filename)

def crop_img_n_get_date(images_directory, date_time_regex, img_crop_end_regex):
    
    """
    Crop the Image and Get date
    ---------------------------
    This method is used to crop the
    images to a standard size and then
    extracts the dates from the text
    of the images.

    Parameters
    ----------
    images_directory : path
        It is the path of images
        folder.
    date_time_regex : str
        Regex to extract the date
        and time from the text.
    img_crop_end_regex : str
        Regex to extract the end
        line of image till where
        the image is to be cropped.
    """
    
    # Declare an empty list to store the image filenames and their associated date and time information
    image_data_list = []
        
    # crop the images to the specified start and end points
    # iterate through the images extracted in the folder
    for img in os.listdir("images"):
        
        # get the complete image path
        filename = os.path.join(images_directory, img)
        
        # Load the image
        img = cv2.imread(filename)

        # Convert the image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Get the text from the image
        text = pytesseract.image_to_string(gray)
        
        # find date and time from the image text
        matches = re.findall(date_time_regex, text)
        if matches:
            datetime_str = matches[0]
        else:
            datetime_str=""
                
        # If a valid datetime string was found, convert it to a datetime object and add it to the image_data_list list
        if datetime_str:
            
            # different formatting for different datetime formats
            try:
                datetime_obj = datetime.strptime(datetime_str, '%m/%d/%y, %I:%M %p')
            except:
                try:
                    datetime_obj = datetime.strptime(datetime_str, '%d/%m/%y, %I:%M %p')
                except:
                    datetime_obj = datetime.strptime(datetime_str, '%d/%m/%y, %H:%M')

            # store image full path and datetime to the image data list
            image_data_list.append((filename, datetime_obj))

        # Find the start and end positions of the text
        start = re.search(date_time_regex, text).start(0)
        end = re.search(img_crop_end_regex, text).start(0)

        # conditions to handle cropping for images with different dimensions
        if int(start)<5:
            
            # Crop the image based on the start and end positions
            cropped_img = img[int(start):int(end)+900, :]
            
        elif int(start)>10 and int(start)<45:
            
            # Crop the image based on the start and end positions
            cropped_img = img[int(start)+600:int(end)+1250, :]
            
        elif int(start)>=50:
            
            # Crop the image based on the start and end positions
            cropped_img = img[int(start)+700:int(end)+1200, :]
            
        else:
            
            # Crop the image based on the start and end positions
            cropped_img = img[int(start):int(end)+700, :]

        # resize the image to standardize all images
        resized_img = cv2.resize(cropped_img, (700, 300))
        
        # save the cropped and resized images back to the folder
        cv2.imwrite(filename, resized_img)
        
    # Sort the image_data_list list by datetime
    image_data_list.sort(key=lambda x: x[1])

    # seperate list for sorted images
    image_list = [x[0] for x in image_data_list]
    
    # seperate list for sorted date_list
    date_list = [x[1] for x in image_data_list]
    
    return image_data_list, image_list, date_list
        
def create_pdf(image_list, image_data_list, output_path, date_list):
    
    """
    Create Final PDF file
    ---------------------------
    This method is used to create a
    PDF file based on sorted images
    where each page of the PDF has the
    images and dates related to one week.

    Parameters
    ----------
    image_list : list
        It is the sorted list of
        all the images.
    image_data_list : list
        It is the sorted list of
        all images and their datetime
        object.
    output_path : path
        It is the path of the output
        PDF file.
    date_list : list
        It is the sorted list of
        all the dates.
    """
    
    # Create a new PDF file
    pdf_canvas = canvas.Canvas(output_path)

    # Set the font for the date and week number
    pdf_canvas.setFont('Helvetica', 12)

    # Get the total number of pages i.e. total number of weeks as each page should have data of one week
    week_numbers = set([date_obj.strftime("%U") for date_obj in date_list])
    num_weeks = len(week_numbers)

    # Loop through number of weeks
    for i in range(0,num_weeks):
        
        # Only add a new page after the first iteration
        if i > 0:
            
            # Add a new page
            pdf_canvas.showPage()

        # get images of specific week
        img_week_specific_list = [image_path for image_path, date in image_data_list if int((date.day - 1) // 7 + 1) == int(i+1)]
        
        # get the start index of images for specific week
        start_index = image_list.index(img_week_specific_list[0])
        
        # get the end index of images for specific week
        end_index = image_list.index(img_week_specific_list[-1])
        
        # Get the images and their dates for a specific week based on the start and end indexes
        page_images = image_data_list[start_index:end_index+1]

        # Draw the week number at the top of the page
        pdf_canvas.drawString(275, 800, "Week " + str(i+1))

        # Default x and y coordinates
        x_pos = 50
        y_pos = 780
 
        # iterate through images for specific week for a page
        for idx in range(len(page_images)):
            
            # Get the image and its date
            image_path, image_date = page_images[idx]

            # Open the image and resize it to fit on the page
            img = Image.open(image_path)
            img.thumbnail((220, 220))
            
            # Draw dates and images on the left half of the PDF
            if idx%2 == 0:
                
                # set y co-ordinates
                y = (65*idx)
                
                # Draw the date above the image
                pdf_canvas.drawString(x_pos, y_pos-y, image_date.strftime("%B %d, %Y"))
                
                # Draw the image
                pdf_canvas.drawImage(img.filename, x_pos, y_pos-(y+100), width=img.width, height=img.height)
                
            # # Draw dates and images on the right half of the PDF
            else:
                
                # set y co-ordinates
                y=(65*(idx-1))
                
                # Draw the date above the image
                pdf_canvas.drawString(x_pos+300, y_pos-y, image_date.strftime("%B %d, %Y"))
                
                # Draw the image
                pdf_canvas.drawImage(img.filename, x_pos+300, y_pos-(y+100), width=img.width, height=img.height)

    # Save the PDF
    pdf_canvas.save()

def main_caller():
    
    """
    Main calling function
    -----------------------------
    It is the main calling function
    which has all the logic implemented.
    """
    
    logger = create_logging()
    
    logger.info("Process started...")
    
    # Define the path to the Poppler bin directory
    poppler_path = os.path.join("poppler-0.68.0","bin")

    # Define the PDF file path
    input_pdf_path = "Shuffled_images.pdf"
    
    # Define the path where images from PDF are stored
    images_directory = "images"
    
    # regex to get date and time from text
    date_time_regex = r"\b\d{1,2}/\d{1,2}/\d{2}(?:\d{2})?, \d{1,2}:\d{2}(?::\d{2})?(?: AM| PM)?\b"
    
    # regex to get end line for the image crop
    img_crop_end_regex = r"(Your ride|You rated|Yourated)"
    
    # output PDF path
    output_pdf = "Result.pdf"
    
    # create image directory if it doesnt exists
    if not os.path.exists(images_directory):
        os.makedirs(images_directory)
    
    logger.info("Extracting images from PDF...")
    
    # get images from PDF and store them to the directory
    get_img_from_pdf(images_directory, input_pdf_path, poppler_path)
    
    logger.info("All images from PDF extracted successfully and stored it to disk...")
    logger.info("Cropping all images to standardize the size and extracting the dates from the images...")
    
    # crop the images and get dates from the text
    image_data_list , image_list, date_list = crop_img_n_get_date(images_directory, date_time_regex, img_crop_end_regex)

    logger.info("Creating a PDF with sorted images...")
    
    # create the PDF file
    create_pdf(image_list, image_data_list, output_pdf, date_list)
    
    # delete the image directory
    shutil.rmtree(images_directory)
    
    logger.info("Output PDF file created and saved successfully...")
    logger.info("Process ended...")
    
if __name__ == "__main__":
    
    # call the main calling function
    main_caller()

