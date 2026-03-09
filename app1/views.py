from datetime import datetime
from django.shortcuts import redirect, render
from django.http import HttpResponseNotFound,HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import os
import json
import requests
import markdown

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.template.loader import get_template

# These heavy imports are now inside functions to save memory
# import joblib
# import pandas as pd
# import fitz
# from xhtml2pdf import pisa

from django.http import HttpResponse
from myproject import settings
from .models import CustomUser, Prediction, ChatSession


# Create your views here.

def load_ml_model():
    """Helper function to load the pre-trained model and encoders on demand."""
    import joblib # Import inside function to save memory
    global _lgbm_model, _encoders, _cat_features
    if _lgbm_model is None:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MODEL_DIR = os.path.join(BASE_DIR, 'app1', 'model')
        try:
            _lgbm_model = joblib.load(os.path.join(MODEL_DIR, 'lgbm_model.joblib'))
            _encoders = joblib.load(os.path.join(MODEL_DIR, 'encoders.joblib'))
            _cat_features = joblib.load(os.path.join(MODEL_DIR, 'cat_features.joblib'))
            print("Pre-trained model and encoders loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load pre-trained model: {e}")
    return _lgbm_model, _encoders, _cat_features


def home(request):
    return render(request,'loginPage/Home.html')


def login(request):
     if request.method=="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            # User is authenticated
            auth_login(request,user)
            my_message = "You are successfully logged in.Now you are ready for Prediction "
            messages.success(request, my_message)
            return redirect('prediction')
            #return render(request,'loginPage/prediction.html',context1)  # Redirect to the 'prediction' URL
        else:
             messages.error(request, "Invalid username or password")  # Use Django messages
     else: #This is where you would put the redirect message
       if not request.user.is_authenticated:
           messages.error(request, 'Please log in to view the page.')
     
     return render(request,'loginPage/login.html')


def signup(request):
    if request.method=="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        confirm_password=request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        dob_str = request.POST.get('dob')  # Get the date of birth as a string
        if confirm_password==password:
            try:
                user = User.objects.create_user(username=username, password=password, email=email)
                #user.save()
                if dob_str:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                else:
                    dob = None
                custom_user = CustomUser.objects.create(user=user, email=email,first_name=first_name,last_name=last_name,gender=gender,dob=dob) # Create the custom user
                custom_user.save()
                
                messages.success(request,"Your Account created sucessfully Login Now")
                login(request, user)
                return redirect('login')
            except:
                messages.error(request,"User already exists")
        else:
            messages.error(request,"Passwords does not matched")   
    return render(request,'loginPage/signup.html')


def logout(request):
    auth_logout(request)
    return redirect('home')

@login_required(login_url='login')  # Correct usage
def about(request):
    return render(request,'loginPage/about_us.html')



@login_required(login_url='login')
def records(request):
    predictions = list(Prediction.objects.filter(user=request.user).order_by('-prediction_date'))
    
    comparisons = []
    insights = []
    trend_insights = []
    
    # Analyze changes between latest and previous
    if len(predictions) >= 2:
        latest = predictions[0]
        # Compare with the previous one
        previous = predictions[1]
        
        compare_fields = ['n_days', 'age', 'bilirubin', 'cholesterol', 'albumin', 'copper', 'alk_phos', 'sgot', 'tryglicerides', 'platelets', 'prothrombin']
        field_names = {
            'n_days': 'N_Days', 'age': 'Age', 'bilirubin': 'Bilirubin', 'cholesterol': 'Cholesterol', 
            'albumin': 'Albumin', 'copper': 'Copper', 'alk_phos': 'Alk. Phos.', 
            'sgot': 'SGOT', 'tryglicerides': 'Triglycerides', 'platelets': 'Platelets', 
            'prothrombin': 'Prothrombin Time'
        }
        
        normal_ranges = {
            'bilirubin': (0.1, 1.2), 'cholesterol': (0, 200), 'albumin': (3.5, 5.5),
            'copper': (70, 140), 'alk_phos': (40, 130), 'sgot': (10, 45),
            'tryglicerides': (0, 150), 'platelets': (150, 450), 'prothrombin': (11.0, 13.5)
        }
        
        all_normal = True
        for field, (min_val, max_val) in normal_ranges.items():
            val = getattr(latest, field)
            if val is None or not (min_val <= val <= max_val):
                all_normal = False
                break
                
        if all_normal:
            insights.append({
                'type': 'all_normal',
                'text': 'All your clinical values are currently within the healthy normal range! Keep up the good work.'
            })

        for field in compare_fields:
            latest_val = getattr(latest, field)
            prev_val = getattr(previous, field)
            
            if latest_val is None or prev_val is None:
                continue
                
            diff = latest_val - prev_val
            status = 'stable'
            if diff > 0:
                status = 'increased'
            elif diff < 0:
                status = 'decreased'
                
            comparisons.append({
                'parameter': field_names[field],
                'previous': prev_val,
                'current': latest_val,
                'status': status,
                'status_class': 'increased' if diff > 0 else ('decreased' if diff < 0 else 'stable'),
                'diff': round(abs(diff), 2) if isinstance(diff, float) else abs(diff)
            })
            
            insight_type = 'neutral'
            if diff == 0:
                insight_type = 'stable'
            elif field in normal_ranges:
                min_val, max_val = normal_ranges[field]
                def dist(v): return max(0, min_val - v, v - max_val)
                old_dist = dist(prev_val)
                new_dist = dist(latest_val)
                
                if new_dist < old_dist:
                    insight_type = 'positive'
                elif new_dist > old_dist:
                    insight_type = 'negative'
                else:
                    insight_type = 'positive' if new_dist == 0 else 'negative'
            else:
                insight_type = 'neutral'
            
            if diff == 0:
                text = f"{field_names[field]} levels are stable compared to the previous record."
            else:
                text = f"Your {field_names[field]} level {status} compared to the previous record."
                if insight_type == 'positive':
                    text = f"Your {field_names[field]} level {status} and is trending positively towards normal range."
                elif insight_type == 'negative':
                    text = f"Your {field_names[field]} level {status} and is trending negatively away from normal."
            
            # Don't clutter if everything is normal and this is just stable, to avoid 10 lines of "stable"
            if not (all_normal and insight_type == 'stable'):
                insights.append({'type': insight_type, 'text': text})

    # Prepare datasets for visualization
    chart_data = []
    for p in reversed(predictions):
        chart_data.append({
            'date': p.prediction_date.strftime('%Y-%m-%d %H:%M'),
            'n_days': p.n_days,
            'age': p.age,
            'bilirubin': p.bilirubin,
            'cholesterol': p.cholesterol if p.cholesterol is not None else 0,
            'albumin': p.albumin,
            'copper': p.copper if p.copper is not None else 0,
            'alk_phos': p.alk_phos if p.alk_phos is not None else 0,
            'sgot': p.sgot if p.sgot is not None else 0,
            'tryglicerides': p.tryglicerides if p.tryglicerides is not None else 0,
            'platelets': p.platelets,
            'prothrombin': p.prothrombin,
            'result': p.prediction_result
        })

    if len(predictions) >= 3:
        plat = [p.platelets for p in reversed(predictions)]
        if all(plat[i] >= plat[i-1] for i in range(1, len(plat))) and plat[-1] > plat[0]:
            trend_insights.append("Platelet count has increased gradually over your recent records.")
        elif all(plat[i] <= plat[i-1] for i in range(1, len(plat))) and plat[-1] < plat[0]:
            trend_insights.append("Platelet count has decreased gradually over your recent records.")
        
        alb = [p.albumin for p in reversed(predictions)]
        if max(alb) - min(alb) < 0.2:
            trend_insights.append("Albumin levels are stable over your recent predictions.")

    context = {
        'predictions': predictions,
        'comparisons': comparisons,
        'insights': insights,
        'trend_insights': trend_insights,
        'chart_data_json': json.dumps(chart_data)
    }
    return render(request, 'loginPage/records.html', context)


@login_required(login_url='login')
def delete_selected_predictions(request):
    if request.method == 'POST':
        prediction_ids = request.POST.getlist('prediction_ids')  # Get list of selected prediction IDs
        if prediction_ids:  # Check if any predictions were selected
            # Delete predictions for the current user and matching selected IDs in a single database query
            deleted_count, _ = Prediction.objects.filter(user=request.user, id__in=prediction_ids).delete()

            if deleted_count > 0:
                messages.success(request, f"{deleted_count} prediction(s) deleted successfully!")
            else:
                messages.warning(request, "No predictions selected or you don't have permission to delete them.")


    return redirect('records')





@login_required(login_url='login')
def prediction(request):
    import pandas as pd # Import inside function to save memory
    error_message = None  # Initialize error_message here
    if request.method == 'POST':
        try:
            # Get data from the form
            n_days = int(request.POST.get('n_days'))
            status = request.POST.get('status')
            drug = request.POST.get('drug')
            age = int(request.POST.get('age'))*1006
            sex = request.POST.get('sex')
            ascites = request.POST.get('ascites')
            hepatomegaly = request.POST.get('hepatomegaly')
            spiders = request.POST.get('spiders')
            edema = request.POST.get('edema')
            bilirubin = float(request.POST.get('Bilirubin'))
            cholesterol = float(request.POST.get('Cholesterol'))
            albumin = float(request.POST.get('Albumin'))
            copper = float(request.POST.get('Copper'))
            alk_phos = float(request.POST.get('Alk_Phos'))
            sgot = float(request.POST.get('SGOT'))
            tryglicerides = float(request.POST.get('Tryglicerides'))
            platelets = float(request.POST.get('Platelets'))
            prothrombin = float(request.POST.get('Prothrombin'))




            # Create a dictionary with the input data
            input_data = {
                'N_Days': [n_days],
                'Status': [status],
                'Drug': [drug],
                'Age': [age],
                'Sex': [sex],
                'Ascites': [ascites],
                'Hepatomegaly': [hepatomegaly],
                'Spiders': [spiders],
                'Edema': [edema],
                'Bilirubin': [bilirubin],
                'Cholesterol': [cholesterol],
                'Albumin': [albumin],
                'Copper': [copper],
                'Alk_Phos': [alk_phos],
                'SGOT': [sgot],
                'Tryglicerides': [tryglicerides],
                'Platelets': [platelets],
                'Prothrombin': [prothrombin]
            }

            # Create a Pandas DataFrame from the input data
            input_df = pd.DataFrame(input_data)

            # Lazy load the model and encoders
            lgbm_model, encoders, _ = load_ml_model()

            if lgbm_model and encoders:
                # Preprocess the input data using saved encoders
                for col, le in encoders.items():
                    if col in input_df.columns:
                        # Handle unseen labels by defaulting to the first class if necessary
                        val = str(input_df[col].iloc[0])
                        if val not in le.classes_:
                             # If unseen, map to the most frequent or first class
                             input_df[col] = le.transform([le.classes_[0]])
                        else:
                             input_df[col] = le.transform([val])

                # Make prediction using the loaded model
                prediction_result = lgbm_model.predict(input_df)[0]
            else:
                raise Exception("ML Model is not loaded.")
            
            # Check for "Normal" result based on standard clinical ranges
            is_normal = (
                0.1 <= bilirubin <= 1.2 and
                cholesterol <= 200 and
                3.5 <= albumin <= 5.5 and
                70 <= copper <= 140 and
                40 <= alk_phos <= 130 and
                10 <= sgot <= 45 and
                tryglicerides <= 150 and
                150 <= platelets <= 450 and
                11.0 <= prothrombin <= 13.5
            )

            stage = ""
            if is_normal:
                stage = "Normal"
            elif prediction_result == 1:
                stage = "Intial stage"
            elif prediction_result == 2:
                stage = "Intermediate stage"
            else:
                stage = "End stage"
            
            print(f"Model Prediction: {prediction_result},Stage: {stage}")

 



            # Save prediction to database
            prediction = Prediction(
                user=request.user,
                n_days=n_days,
                status=status,
                drug=drug,
                age=int(age/1006),
                sex=sex,
                ascites=ascites,
                hepatomegaly=hepatomegaly,
                spiders=spiders,
                edema=edema,
                bilirubin=bilirubin,
                cholesterol=cholesterol,  # Include all fields, even if they might be missing
                albumin=albumin,
                copper=copper,
                alk_phos=alk_phos,
                sgot=sgot,
                tryglicerides=tryglicerides,
                platelets=platelets,
                prothrombin=prothrombin,                
                prediction_result=stage,
            )
            prediction.save()

            # Pass the prediction result to the template
            context = {'prediction':stage, 'input_data': input_data} # Example context
            return render(request, 'loginPage/prediction.html', context)
            #return render(request, 'loginPage/prediction.html', {'prediction': prediction_result})

        except (ValueError, KeyError) as e:  # Catch ValueError for invalid input and KeyError for missing fields
            error_message = f"Invalid input or missing fields: {e}"  # Store the error message  # Provide informative error message
            #return redirect('prediction') # Redirect back to the form
        except Exception as e: # General exception handling to catch unexpected issues
            error_message = f"An error occurred during prediction: {e}"
            # log the error or perform other handling
    context = {'error_message': error_message}  # Add error_message to the context
    return render(request, 'loginPage/prediction.html', context)
    #return render(request, 'loginPage/prediction.html')  # Render the form template if not a POST request



        # Add all prediction fields to the document





















@login_required(login_url='login')
def download_pdf(request):
    from xhtml2pdf import pisa # Import inside function to save memory
    prediction_id = request.GET.get('id')
    if prediction_id:
        predictions = Prediction.objects.filter(user=request.user, id=prediction_id)
    else:
        predictions = Prediction.objects.filter(user=request.user).order_by('-prediction_date')
        
    template_path = 'loginPage/pdf_template.html'
    context = {'predictions': predictions, 'user': request.user}
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="report.pdf"'

    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



def link_callback(uri, rel):
    # use short variable names, safely fallback if not defined in settings.py
    sUrl = getattr(settings, 'STATIC_URL', '/static/')
    if not sUrl.startswith('/'):
        sUrl = '/' + sUrl
        
    sRoot = getattr(settings, 'STATIC_ROOT', None)
    if not sRoot:
        sRoot = settings.STATICFILES_DIRS[0]

    mUrl = getattr(settings, 'MEDIA_URL', '/media/')
    mRoot = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))

    # ensure uri has leading slash for matching
    if not uri.startswith('/') and not uri.startswith('http'):
        uri = '/' + uri

    # convert URIs to absolute system paths
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, "", 1))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, "", 1))
    else:
        return uri  # handle absolute uri (ie: http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
            return uri
    return path



 # Import your CustomUser model

@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        # Get data from the form
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        dob_str = request.POST.get('dob')
        email = request.POST.get('email')
        update_password = request.POST.get('update_password') == 'on'
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if update_password:
            if new_password and new_password == confirm_password:
                request.user.set_password(new_password)
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
            else:
                messages.error(request, "Passwords do not match or cannot be empty.")
                return redirect('edit_profile')

        # Update the User model
        request.user.username = username
        request.user.email = email
        request.user.save()

        # Update the CustomUser model
        if hasattr(request.user, 'custom_user'):
            custom_user = request.user.custom_user
        else:
            custom_user = CustomUser(user=request.user)
        custom_user.first_name = first_name
        custom_user.last_name = last_name
        custom_user.gender = gender

        if dob_str:
            custom_user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        else:
            custom_user.dob = None

        custom_user.save()

        messages.success(request, "Your profile has been updated successfully!")
        return redirect('prediction')  # Redirect to the profile page or any other page

    # If it's a GET request, pre-populate the form
    return render(request, 'loginPage/edit_profile.html', {'user': request.user})


# --- QWEN 2.5 AI CHAT INTEGRATION ---

# Setup the requests details to point to Hugging Face
API_URL = "https://router.huggingface.co/v1/chat/completions"

def extract_text_from_pdf(pdf_file):
    """Helper function to read text from an uploaded PDF using PyMuPDF."""
    import fitz # Import inside function to save memory
    text = ""
    # Open the uploaded PDF stream
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

@csrf_exempt
@login_required(login_url='login')
def list_chat_sessions(request):
    """Returns a list of chat sessions for the current user."""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:15]
    data = [
        {
            "id": s.id,
            "title": s.title,
            "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M"),
        } for s in sessions
    ]
    return JsonResponse({"sessions": data})

@csrf_exempt
@login_required(login_url='login')
def load_chat_session(request, session_id):
    """Loads a specific chat session's history."""
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
        return JsonResponse({
            "id": session.id,
            "title": session.title,
            "history": session.history
        })
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

@csrf_exempt
@login_required(login_url='login')
def delete_chat_session(request, session_id):
    """Deletes a specific chat session."""
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
        session.delete()
        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

@csrf_exempt
def ai_chat(request):
    """
    Handles POST requests from the frontend chat interface to chat with Qwen 2.5.
    Can read an uploaded PDF file and maintain chat history.
    """
    if request.method == "POST":
        # Get token from settings
        hf_token = getattr(settings, 'HF_TOKEN', '')
        if not hf_token:
            return JsonResponse({"error": "AI Chat is currently unavailable (API Token missing). Please contact the administrator."}, status=503)
        
        headers = {
            "Authorization": f"Bearer {hf_token}",
        }
        
        try:
            user_message = request.POST.get("message", "Hello")
            chat_history_str = request.POST.get("history", "[]")
            session_id = request.POST.get("session_id")
            chat_history = json.loads(chat_history_str)

            # Initialize system prompt if history is empty
            if not chat_history:
                chat_history.append({
                    "role": "system",
                    "content": """
            You are **Dr. Qwen**, a highly intelligent, compassionate, and engaging AI hepatology assistant inside this Liver Cirrhosis health platform.

            Your mission is to deliver a **premium conversational experience**—similar to the world’s best AI assistants—while providing expert medical guidance with a human touch.

            ━━━━━━━━━━━━━━━━━━━━
            🧠 CORE ROLE
            ━━━━━━━━━━━━━━━━━━━━
            • Explain liver health, lab reports, and cirrhosis concepts in **clear, human-friendly language**.
            • Translate complex numerical data into **meaningful insights**.
            • Support users emotionally and intellectually through their health journey.

            ━━━━━━━━━━━━━━━━━━━━
            🚀 HOW I HELP USERS
            ━━━━━━━━━━━━━━━━━━━━
            1. **Medical Insight & Education**:
               - Explain what liver cirrhosis is: *"A condition where healthy liver tissue is replaced by scar tissue, leading to impaired function."*
               - Explain complications like portal hypertension or liver failure in simple terms.
            2. **Lifestyle Support**:
               - **Nutrition**: Provide science-backed suggestions for liver-friendly diets (fruits, veggies, lean proteins).
               - **Hydration**: Explain why water is crucial for liver detoxification.
               - **Habits**: Recommend avoiding alcohol, managing stress, and regular exercise.
            3. **Empathetic Companion**:
               - **Active Listening**: Respect user concerns.
               - **Anxiety Reduction**: Use reassuring language.
               - Example: *"I understand you might be feeling anxious about your results. Let’s break them down together. 🤝"*

            ━━━━━━━━━━━━━━━━━━━━
            💬 PERSONALITY & TONE
            ━━━━━━━━━━━━━━━━━━━━
            • **Warm & Empathetic**: A knowledgeable doctor who genuinely cares.
            • **Professional yet Accessible**: Friendly, supportive, and curious.
            • **Proactive**: If values look concerning, suggest specific questions for their doctor.

            ━━━━━━━━━━━━━━━━━━━━
            ✨ COMMUNICATION STYLE
            ━━━━━━━━━━━━━━━━━━━━
            • Use **Markdown formatting** (Bold terms, Italics for emphasis).
            • Use **Emoji Accents** professionally (🩺, 📊, 🌱, 🧠, 💧, ✨).
            • Keep it interactive—never just lecture; always engage.

            ━━━━━━━━━━━━━━━━━━━━
            🔍 REPORT ANALYSIS MODE
            ━━━━━━━━━━━━━━━━━━━━
            When a report is uploaded:
            1. **Examine** values carefully.
            2. **Highlight** markers (Bilirubin, Albumin, ALT, etc.).
            3. **Analyze Patterns**: Identify what might suggest inflammation or damage.
            4. **Gentle Tone**: Use phrases like *"may suggest"* or *"appears elevated"* instead of scary certainties.

            ━━━━━━━━━━━━━━━━━━━━
            📊 RESPONSE STRUCTURE
            ━━━━━━━━━━━━━━━━━━━━
            Use structured sections for readability:
            ### 🩺 Medical Insight
            ### 📊 Observations & Summary
            ### 🌱 Lifestyle Guidance
            ### ❓ Let's Explore Further

            ━━━━━━━━━━━━━━━━━━━━
            🛡️ SAFETY RULES
            ━━━━━━━━━━━━━━━━━━━━
            • Never provide a definitive diagnosis.
            • Avoid medical certainty; use educational language.
            • **Always** encourage consultation with a professional medical team.
            • Remind the user: *"I am an AI assistant, here for information and support."*

            ━━━━━━━━━━━━━━━━━━━━
            💡 EXPERIENCE GOAL
            ━━━━━━━━━━━━━━━━━━━━
            Your responses should feel:
            • **Engaging** like a conversation.
            • **Visually clear** and structured using Markdown.
            • **Helpful and reassuring** but professional.
            • **Intelligent** but easy to understand for everyone.
            The user should feel supported, informed, and comfortable asking follow-up questions.
            """
                })

            context_message = ""
            
            # Check if a PDF was uploaded
            if "pdf_document" in request.FILES:
                pdf_file = request.FILES["pdf_document"]
                pdf_text = extract_text_from_pdf(pdf_file)
                # Truncate text to avoid blowing up the token limit
                pdf_text = pdf_text[:12000] 
                context_message = f"I have uploaded a medical report. Here is the text extracted from it:\n\n---\n{pdf_text}\n---\n\n"

            # Combine any PDF text with the user's actual question
            final_user_content = context_message + user_message

            # Add this turn to chat history
            chat_history.append({"role": "user", "content": final_user_content})

            # Call Qwen 2.5 7B Instruct via requests
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct:together",
                "messages": chat_history,
                "max_tokens": 1000,
                "temperature": 0.3
            }
            response = requests.post(API_URL, headers=headers, json=payload)
            response_json = response.json()

            # Extract the AI's reply
            if "choices" not in response_json or len(response_json["choices"]) == 0:
                raise Exception(f"Invalid API response: {response_json}")
            
            ai_reply_raw = response_json['choices'][0]['message']['content']
            
            # Convert Markdown to HTML for a rich, interactive UI (Headings, Bold, Lists, etc.)
            ai_reply = markdown.markdown(ai_reply_raw, extensions=['extra', 'nl2br', 'sane_lists'])
            
            # Save the AI's raw reply to history so the loop continues
            chat_history.append({"role": "assistant", "content": ai_reply_raw})

            # Prepare history for the frontend:
            # We want to keep the system prompt if it exists, plus the final user/assistant exchange.
            system_msgs = [msg for msg in chat_history if msg.get("role") == "system"]
            clean_history = system_msgs + chat_history[-2:] if len(chat_history) >= 2 else chat_history
            
            # --- Session Management ---
            # Automatically save/update session if user is logged in
            if request.user.is_authenticated:
                # Convert string "null" from JS to actual None
                if session_id == "null" or session_id == "undefined":
                    session_id = None
                
                if session_id:
                    try:
                        session = ChatSession.objects.get(id=session_id, user=request.user)
                        session.history = clean_history
                        session.save()
                    except (ChatSession.DoesNotExist, ValueError):
                        session_id = None # Fallback to creating new

                if not session_id:
                    # Create a title from the first message
                    title = user_message[:40] + ("..." if len(user_message) > 40 else "")
                    session = ChatSession.objects.create(
                        user=request.user,
                        title=title,
                        history=clean_history
                    )
                    session_id = session.id
                    
                    # ENFORCE LIMIT: Keep only latest 15 sessions
                    excess_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[15:]
                    for s in excess_sessions:
                        s.delete()

            return JsonResponse({
                "reply": ai_reply,
                "history": clean_history,
                "session_id": session_id
            })

        except Exception as e:
             # Make sure to look at your Django terminal if there's an error
            print(f"AI Chat Error: {str(e)}")
            return JsonResponse({"error": "I'm sorry, I encountered an error connecting to the AI. " + str(e)}, status=500)

    return JsonResponse({"error": "Only POST method is allowed"}, status=400)
