/* ============================================================
   SMART BUS HOME PAGE
============================================================ */


/* ============================================================
   NUMBER COUNTER
============================================================ */

function animateCounter(element) {

    if (!element) {
        return;
    }

    const target =
        Number(element.dataset.value) || 0;

    const duration = 900;

    const startTime =
        performance.now();


    function update(currentTime) {

        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(elapsed / duration, 1);

        const eased =
            1 - Math.pow(1 - progress, 3);

        const value =
            Math.round(target * eased);

        element.textContent =
            String(value).padStart(2, "0");


        if (progress < 1) {

            requestAnimationFrame(update);

        }

    }

    requestAnimationFrame(update);
}



/* ============================================================
   START COUNTERS
============================================================ */

function startCounters() {

    document
        .querySelectorAll("[data-value]")
        .forEach(element => {

            animateCounter(element);

        });

}



/* ============================================================
   SMALL HERO MOTION
============================================================ */

function initialiseHeroMotion() {

    const visual =
        document.querySelector(".hero-visual");

    if (!visual) {
        return;
    }


    visual.addEventListener(
        "mousemove",
        event => {

            const rect =
                visual.getBoundingClientRect();

            const x =
                (event.clientX - rect.left)
                / rect.width;

            const y =
                (event.clientY - rect.top)
                / rect.height;


            const moveX =
                (x - 0.5) * 8;

            const moveY =
                (y - 0.5) * 8;


            visual.style.transform =
                `perspective(1000px)
                 rotateY(${moveX}deg)
                 rotateX(${-moveY}deg)`;

        }
    );


    visual.addEventListener(
        "mouseleave",
        () => {

            visual.style.transform =
                "perspective(1000px) rotateY(0deg) rotateX(0deg)";

        }
    );

}



/* ============================================================
   INITIALISE
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        startCounters();

        initialiseHeroMotion();

    }
);