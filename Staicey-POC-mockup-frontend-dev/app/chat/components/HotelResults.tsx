"use client";

import { FC, useEffect, useRef, useState, useCallback } from "react";
import { MapPinIcon, StarIcon, PhoneIcon, CheckCircle, ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import { Hotel } from "@/lib/types";
import Link from "next/link";
import { Loader } from "@googlemaps/js-api-loader";
import { createSafeExternalHref } from "@/lib/utils/linkValidation";
import useEmblaCarousel from 'embla-carousel-react';
import Autoplay from 'embla-carousel-autoplay';

type Props = {
  hotels: Hotel[];
  mapEmbedUrl: string;
};

// Hotel Image Carousel Component
const HotelImageCarousel: FC<{ images: string[]; hotelName: string }> = ({ images, hotelName }) => {
  const [emblaRef, emblaApi] = useEmblaCarousel(
    { 
      loop: true, 
      // align: 'center',
      // duration: 20,
      // startIndex: 0,
      // skipSnaps: false,
      // inViewThreshold: 0.7
    },
    [Autoplay({ 
      delay: 10000, 
      // stopOnInteraction: false, 
      // stopOnMouseEnter: true,
      // playOnInit: true
    })]
  );
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [scrollSnaps, setScrollSnaps] = useState<number[]>([]);
  const [failedImages, setFailedImages] = useState<Set<number>>(new Set());

  const onSelect = useCallback(() => {
    if (!emblaApi) return;
    setSelectedIndex(emblaApi.selectedScrollSnap());
  }, [emblaApi]);

  const scrollTo = useCallback((index: number) => {
    if (!emblaApi) return;
    emblaApi.scrollTo(index);
  }, [emblaApi]);

  const scrollPrev = useCallback(() => {
    if (!emblaApi) return;
    emblaApi.scrollPrev();
  }, [emblaApi]);

  const scrollNext = useCallback(() => {
    if (!emblaApi) return;
    emblaApi.scrollNext();
  }, [emblaApi]);

  const handleImageError = useCallback((e: React.SyntheticEvent<HTMLImageElement>, index: number) => {
    // Mark this image as failed
    setFailedImages(prev => new Set([...Array.from(prev), index]));
    
    // Try to find another valid image from the original array
    if(index === 0) {
      e.currentTarget.src = "/assets/images/images/hotel-template.jpg";
      return;
    }
    else if (Array.isArray(images) && images.length > 0) {
      for (let i = index - 1; i >= 0; i--) {
        if (i !== index && !failedImages.has(i)) {
          e.currentTarget.src = images[i];
          return;
        }
      }
    }
    
    // If no other valid images found, use template image
    e.currentTarget.src = "/assets/images/images/hotel-template.jpg";
  }, [images, failedImages]);

  // Filter out failed images and ensure template image is available
  let validImages: string[] = [];
  
  // If no images provided or empty array, use template image
  if(!Array.isArray(images) || images.length === 0) {
    validImages = ["/assets/images/images/hotel-template.jpg"];
  } else {
    validImages = images.filter((_, index) => !failedImages.has(index));
    
    // If all images have failed, use template image
    if(validImages.length === 0) {
      validImages = ["/assets/images/images/hotel-template.jpg"];
    }
  }

  useEffect(() => {
    if (!emblaApi) return;
    onSelect();
    setScrollSnaps(emblaApi.scrollSnapList());
    emblaApi.on('select', onSelect);
    return () => {
      emblaApi.off('select', onSelect);
    };
  }, [emblaApi, onSelect]);

  if (!validImages || validImages.length === 0) {
    return (
      <Image
        src="/assets/images/images/hotel-template.jpg"
        alt={hotelName}
        className="w-full h-32 sm:w-48 sm:h-28 lg:w-60 lg:h-52 object-cover rounded-lg"
        width={192}
        height={192}
      />
    );
  }

  return (
    <div className="relative w-full h-36 sm:w-full sm:h-52 lg:w-72 lg:h-48 xl:h-52 rounded-lg overflow-hidden">
      <style jsx>{`
        .embla__viewport {
          overflow: hidden;
          width: 100%;
          height: 100%;
        }
        .embla__container {
          display: flex;
          user-select: none;
          -webkit-touch-callout: none;
          -khtml-user-select: none;
          -webkit-tap-highlight-color: transparent;
          height: 100%;
          transition: transform 0.3s ease-out;
        }
        .embla__slide {
          min-width: 100%;
          position: relative;
          height: 100%;
          transition: all 0.3s ease-out;
          padding: 0;
        }
        .embla__slide__inner {
          overflow: hidden;
          height: 100%;
        }
        .embla__slide img {
          transition: transform 0.3s ease-out;
        }
      `}</style>
      <div className="embla__viewport" ref={emblaRef}>
        <div className="embla__container">
          {validImages.map((image, index) => (
            <div className="embla__slide" key={`image_${index}`} style={{width: '100%', height: '100%'}}>
              <Image src={image} alt={`${hotelName} - Image ${index + 1}`} className="w-full h-full object-cover" onError={(e) => handleImageError(e, index)} width={280} height={240} loading="lazy" />
            </div>
          ))}
        </div>
      </div>

      {/* Navigation arrows */}
      {validImages.length > 1 && (
        <>
          <button
            onClick={scrollPrev}
            className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-1 transition-colors z-10"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={scrollNext}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-1 transition-colors z-10"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </>
      )}

      {/* Dots indicator */}
      {/* {validImages.length > 1 && (
        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex gap-1 z-10">
          {scrollSnaps.map((_, index) => (
            <button
              key={index}
              onClick={() => scrollTo(index)}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === selectedIndex
                  ? 'bg-white'
                  : 'bg-white/50 hover:bg-white/75'
              }`}
            />
          ))}
        </div>
      )} */}
    </div>
  );
};

const HotelResults: FC<Props> = ({ hotels, mapEmbedUrl }) => {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadMap = async () => {
      // Check if API key exists
      if (!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY) {
        console.warn('Google Maps API key not found');
        return;
      }

      const loader = new Loader({
        apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
        version: "weekly",
      });

      try {
        const google = await loader.load();
        
        if (!mapRef.current) return;

        // Calculate bounds from hotel positions
        const bounds = new google.maps.LatLngBounds();
        hotels.forEach((hotel) => {
          if(hotel.position && hotel.position.lat && hotel.position.lng) {
            bounds.extend(new google.maps.LatLng(hotel.position.lat, hotel.position.lng));
          }
        });

        let zoom = 11;

        const map = new google.maps.Map(mapRef.current, {
          center: bounds.getCenter(),
          zoom: zoom,
        });

        // Fit map to bounds with padding
        map.fitBounds(bounds, {
          padding: { top: 50, right: 50, bottom: 50, left: 50 }
        });

        hotels.forEach((hotel) => {
          if(hotel.position == null) return;
          if(hotel.position.lat == null || hotel.position.lng == null) return;
          const markerEl = document.createElement("div");
          markerEl.style.display = "flex";
          markerEl.style.flexDirection = "column";
          markerEl.style.alignItems = "center";
          markerEl.style.textAlign = "center";
          markerEl.style.position = "relative";

          // icon
          const iconImg = document.createElement("img");
          iconImg.src = "/assets/images/icons/hotel-icon.png"; // put in public folder
          iconImg.classList.add("w-10", "h-10", "object-contain");

          // label
          const labelEl = document.createElement("span");
          labelEl.textContent = hotel.name;
          labelEl.classList.add(
            "bg-[#c3308d]",     
            "text-white",     
            "h-6",
            "flex",
            "justify-center",
            "items-center",
            "px-1.5",         // padding left/right ~ 6px
            "py-0.5",         // padding top/bottom ~ 2px
            "rounded-full",        // border-radius
            "text-xs",        // font-size ~ 12px
            "font-bold",      // bold text
            "shadow-md",      // box shadow
            "absolute",       // absolute positioning
            "top-2",         // top: -20px
            "left-8",         // left: 32px
            "whitespace-nowrap", // prevent text wrap
            "border-gray-300",
            "border-1",
          );
          // labelEl.style.transform = "translateX(-50%)";

          markerEl.appendChild(iconImg);
          markerEl.appendChild(labelEl);

          // Custom Overlay
          const overlay = new google.maps.OverlayView();
          overlay.onAdd = function () {
            const panes = overlay.getPanes();
            panes?.overlayMouseTarget?.appendChild(markerEl);
          };
          overlay.draw = function () {
            const projection = overlay.getProjection();
            const position = projection.fromLatLngToDivPixel(
              new google.maps.LatLng(hotel.position.lat, hotel.position.lng)
            );
            if (position) {
              markerEl.style.position = "absolute";
              markerEl.style.left = position.x - 20 + "px"; // center horizontally
              markerEl.style.top = position.y - 40 + "px"; // adjust for icon height
            }
          };
          overlay.onRemove = function () {
            markerEl.parentNode?.removeChild(markerEl);
          };
          overlay.setMap(map);
        });
      } catch (error) {
        console.error('Failed to load Google Maps:', error);
      }
    };

    loadMap();
  }, [hotels]);

  return (
    <div className="flex flex-col gap-4 bg-transparent rounded-lg overflow-hidden">
      {/* Header */}

      <div className="flex flex-col 2xl:flex-row gap-2">
        {/* Hotel list */}
        <div className="flex-1 flex flex-col gap-4 mr-2">
          {hotels.map((hotel:any, index:number) => (
            <div key={hotel.id || `hotel_id_${index}`}>
              <div className="relative bg-transparent w-full max-w-fit px-3 py-2 text-xs sm:text-sm text-gray-800 mb-2">
                <span className="line-clamp-5"><span className="font-semibold text-black">{hotel.name}:</span> {hotel.aiNote}</span>
              </div>
              <div
                className="flex flex-col lg:flex-row gap-1 rounded-xl border border-gray-200 overflow-hidden bg-white shadow-sm"
              >
                {/* Hotel image */}
                <div className="flex justify-center items-center py-2 px-2 sm:py-[0.8rem] sm:px-[1rem]">
                  <HotelImageCarousel images={hotel.imageUrls} hotelName={hotel.name} />
                  {/* <Image src={ Array.isArray(hotel.imageUrls) && hotel.imageUrls.length > 0 && hotel.imageUrls[0] || "/assets/images/images/hotel-template.jpg"} alt={`${hotel.name} - Image`} className="w-48 h-28 object-cover lg:w-60 lg:h-52 max-h-[100%] rounded-lg" onError={(e) => e.currentTarget.src = Array.isArray(hotel.imageUrls) && hotel.imageUrls.length > 1 && hotel.imageUrls[1] || "/assets/images/images/hotel-template.jpg"} width={280} height={240} /> */}
                </div>

                {/* Details */}
                <div className="flex flex-col flex-1 py-2 pl-4 pr-2 lg:pl-0 sm:py-[0.8rem] sm:pr-[1rem] justify-between">
                  <div className="flex flex-1 items-start justify-between flex-col sm:flex-row">
                    <div className="flex flex-col w-full sm:w-2/3 justify-around h-full">
                      <h3 className="font-semibold text-lg sm:text-xl line-clamp-2 capitalize">{hotel.name}</h3>
                      <div className="flex items-center gap-1 text-xs sm:text-sm text-yellow-500 flex-wrap">
                        {Array.from({ length: 5 }).map((_, i) => {
                          const diff = hotel.rating - i;
                          
                          if (diff >= 1) {
                            // Full star
                            return <StarIcon key={i} className="w-4 h-4 fill-current" />;
                          } else if (diff > 0) {
                            // Half star
                            return (
                              <div key={i} className="relative w-4 h-4">
                                <StarIcon className="w-4 h-4 text-gray-300" />
                                <div className="absolute inset-0 overflow-hidden" style={{ width: `${diff * 100}%` }}>
                                  <StarIcon className="w-4 h-4 fill-current" />
                                </div>
                              </div>
                            );
                          } else {
                            // Empty star
                            return <StarIcon key={i} className="w-4 h-4 text-gray-300" />;
                          }
                        })}
                        <span className="text-gray-600 ml-1">
                          {(hotel.rating / 1.0).toFixed(1)} ({hotel.reviews >= 1000 ? `${(hotel.reviews / 1000).toFixed(1)}K` : hotel.reviews?.toLocaleString() || '0'})
                        </span>
                        <span className="text-gray-500 ml-2 uppercase">
                          {hotel.stars && `${hotel.stars}-Star hotel`}
                        </span>
                      </div>
                      <div className="flex flex-col gap-1 mt-1">
                        {hotel.address && (
                          <p className="text-sm text-gray-600 flex items-start gap-1">
                            <MapPinIcon size={12} className="min-w-fit min-h-4 w-4 h-4 text-gray-400" />
                            {hotel.address}
                          </p>
                        )}
                        {hotel.phone && (
                          <p className="text-sm text-gray-600 flex items-center gap-1">
                            <PhoneIcon className="min-w-fit w-4 h-4 text-gray-400" />
                            {hotel.phone}
                          </p>
                        )}
                      </div>
                      {/* Features */}
                      <div className="flex flex-wrap gap-0 mt-1">
                        {hotel.features.map((f:any, index:number) => (
                          index < 7 && <span
                            key={f}
                            className="pr-2 py-1 rounded-full text-xs text-gray-400 flex items-center gap-1"
                          >
                            <CheckCircle className="w-4 h-4 text-gray-400" />
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Price & CTA */}
                    <div className="hidden sm:flex flex-col items-end justify-around h-full gap-2 w-full sm:max-w-[170px] mt-2 sm:mt-0">
                      {/* <div className="text-right flex flex-col justify-between"> */}
                        <p className="text-xs text-gray-400 uppercase">{hotel.price && 'Best Price'}</p>
                        <p className="text-2xl sm:text-3xl font-bold text-green-600">
                          {hotel.price && hotel.price[0] === '$' ? `A${hotel.price}` : hotel.price}
                          {hotel.price && <span className="text-xs text-gray-400">/night</span>}
                        </p>
                        <p className="text-xs text-gray-600 font-semibold">{hotel.roomType}</p>
                        <p className="text-[10px] text-gray-500 text-right">
                          {hotel.source && `Source: `} {(() => {
                            const safeHref = createSafeExternalHref(hotel.sourceUrl);
                            return safeHref ? (
                              <Link href={safeHref} target="_blank" rel="noopener noreferrer">{hotel.source}</Link>
                            ) : (
                              <span>{hotel.source}</span>
                            );
                          })()}
                        </p>
                        <div className="flex flex-col gap-0 items-end">
                          {
                            hotel.extra_prices && 
                            Array.isArray(hotel.extra_prices) && 
                            hotel.extra_prices.length > 0 &&
                              hotel.extra_prices.map((extra_price: any, index: number) => 
                                {
                                  if(index > 1) return null;
                                  const safeHref = createSafeExternalHref(extra_price.source_url);
                                  return safeHref ? (
                                    <p key={index} className="text-sm text-gray-500 italic font-bold p-0 m-0 text-right">
                                      {`A$${extra_price.price} - `}
                                      <Link href={safeHref} target="_blank" rel="noopener noreferrer">{extra_price.source === hotel.name ? "Direct" : extra_price.source}</Link>
                                    </p>
                                  ) : (
                                    <span>{`A$${extra_price.price} - `}{extra_price.source}</span>
                                  );
                                }
                              )
                          }
                        </div>
                        <Link href={hotel.sourceUrl || ""} target="_blank" rel="noopener noreferrer" className="hidden sm:block min-w-fit">
                          <button className={`w-min-[300px] px-4 py-3 sm:px-2 sm:py-1 md:px-4 md:py-2 lg:px-5 lg:py-4 font-bold ${hotel.price ? 'bg-[#c3308d] text-white hover:bg-[#c3308ddd]' : 'bg-gray-300 text-gray-500'}  rounded-full text-xs sm:text-sm  w-full sm:w-auto`} disabled={hotel.price == null}>
                            {hotel.price ? 'Book Now' : 'Unavailable'}
                          </button>
                        </Link>
                      {/* </div> */}
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2 justify-between mt-2">
                    {/* AI note */}
                    {/* <div className="relative bg-[#272d64] rounded-lg w-full max-w-fit sm:w-2/3 px-3 py-2 text-xs sm:text-sm text-white italic mb-1">
                      <span className="line-clamp-2"><span className="font-semibold">Staicey says:</span> {hotel.aiNote}</span>
                      <div className="absolute -bottom-2 left-2 w-0 h-0 border-l-[2px] border-l-transparent border-r-[8px] border-r-transparent border-t-[11px] border-t-[#272d64] rotate-[20deg]"></div>
                    </div> */}
                    <div className="flex justify-center items-center gap-2">
                      {/* Mobile version - Price & CTA */}
                      <div className="flex sm:hidden flex-col xs:flex-row items-start xs:items-center justify-around h-full gap-0 xs:gap-1 sm:gap-2 w-full sm:max-w-[240px] mt-2 sm:mt-0">
                        {/* <div className="text-right flex flex-col justify-between"> */}
                          <p className="text-xs text-gray-400 uppercase">Best Price</p>
                          <p className="text-2xl sm:text-3xl font-bold text-green-600">
                            {hotel.price && hotel.price[0] === '$' ? `A${hotel.price}` : hotel.price}
                            {hotel.price && <span className="text-xs text-gray-400">/night</span>}
                          </p>
                          <p className="text-xs text-gray-600 font-semibold">{hotel.roomType}</p>
                          <p className="text-[10px] text-gray-500 text-left sm:text-right">
                            {hotel.source && `Source: `} {(() => {
                              const safeHref = createSafeExternalHref(hotel.sourceUrl);
                              return safeHref ? (
                                <Link href={safeHref} target="_blank" rel="noopener noreferrer">{hotel.source}</Link>
                              ) : (
                                <span>{hotel.source}</span>
                              );
                            })()}
                          </p>
                        {/* </div> */}
                      </div>
                      <Link href={hotel.sourceUrl || ""} target="_blank" rel="noopener noreferrer" className="block sm:hidden min-w-fit">
                        <button className={`w-min-[300px] px-4 py-3 sm:px-2 sm:py-1 md:px-4 md:py-2 lg:px-5 lg:py-4 font-bold ${hotel.price ? 'bg-[#c3308d] text-white hover:bg-[#c3308ddd]' : 'bg-gray-300 text-gray-500'}  rounded-full text-xs sm:text-sm  w-full sm:w-auto`} disabled={hotel.price == null}>
                          {hotel.price ? 'Book Now' : 'Unavailable'}
                        </button>
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Map */}
        {/* <div className="2xl:w-1/3 h-64 2xl:h-auto">
          <iframe
            src={mapEmbedUrl}
            width="100%"
            height="100%"
            style={{ border: 0 }}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            className="rounded-2xl"
          ></iframe>
        </div> */}
        {hotels.length > 0 && (
          <div ref={mapRef} className="2xl:w-1/3 h-72 2xl:h-auto rounded-lg" />
        )}
      </div>
    </div>
  );
};

export default HotelResults;
