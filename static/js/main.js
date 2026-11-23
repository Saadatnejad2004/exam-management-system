document.addEventListener("DOMContentLoaded", () => {
    // 1. Password Visibility Toggle
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        // Wrap input in a relative container
        const wrapper = document.createElement('div');
        wrapper.className = 'password-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'toggle-password';
        toggleBtn.innerText = 'Show';
        
        toggleBtn.addEventListener('click', () => {
            if (input.type === 'password') {
                input.type = 'text';
                toggleBtn.innerText = 'Hide';
            } else {
                input.type = 'password';
                toggleBtn.innerText = 'Show';
            }
        });

        wrapper.appendChild(toggleBtn);
    });

    // 2. Form Error Animation (Shake effect)
    const errorLists = document.querySelectorAll('.errorlist');
    if (errorLists.length > 0) {
        const form = document.querySelector('form');
        form.style.animation = 'shake 0.4s ease-in-out';
    }
});

// Add CSS animation via JS to avoid cluttering stylesheet
const style = document.createElement('style');
style.innerHTML = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }
`;
document.head.appendChild(style);
